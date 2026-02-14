"""
Joint SRAM Optimization Program
SRAM联合优化程序

This program implements joint optimization for SRAM architecture and transistor parameters:
该程序实现SRAM架构与晶体管参数的联合优化：

- Jointly optimize rows/columns/arrays and transistor parameters
- 同时优化行列数、阵列数量与晶体管参数
- Support multiple algorithms: SA, PSO, SMAC, CBO, RoSE_Opt, MOEAD, MOBO, NSGA-II
- 支持多种算法：SA, PSO, SMAC, CBO, RoSE_Opt, MOEAD, MOBO, NSGA-II
"""

import os
import sys
import time
import numpy as np
import torch
import random
import warnings
import json
import csv
import shutil
from pathlib import Path
import traceback
from datetime import datetime
from typing import List, Tuple, Dict, Any
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")

ROW_CHOICES = [16, 32, 64, 128, 256, 512]
COLUMN_CHOICES = [16, 32, 64, 128, 256, 512]
TOTAL_BITS = 262144

# Import SMAC for Stage 1 optimization
from smac import HyperparameterOptimizationFacade, Scenario
from ConfigSpace import Configuration, ConfigurationSpace
import ConfigSpace.hyperparameters as CSH

SMAC_AVAILABLE = True

# Import path handling
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

# Import utilities
from size_optimization.exp_utils import seed_set, create_directories, ModifiedSRAMParameterSpace, get_params_from_yaml
from utils import estimate_total_area, estimate_bitcell_area

# Import SRAM simulation modules
# 导入SRAM仿真模块
from PySpice.Unit import u_V, u_ns, u_Ohm, u_pF, u_A, u_mA
from sram_compiler.testbenches.sram_6t_core_MC_testbench import Sram6TCoreMcTestbench
from config import SRAM_CONFIG


class ArchitectureConfigurationSpace:
    """
    Architecture configuration space for 32KB (262144-bit) SRAM
    32KB（262144 位）SRAM的架构配置空间
    """

    def __init__(self):
        self.total_bits = TOTAL_BITS
        self.row_choices = ROW_CHOICES
        self.column_choices = COLUMN_CHOICES
        self.max_rows = max(self.row_choices)
        self.max_cols = max(self.column_choices)
        self.min_rows = min(self.row_choices)
        self.min_cols = min(self.column_choices)
        self.valid_configs = self._generate_valid_configurations()

    def _generate_valid_configurations(self) -> List[Dict]:
        """
        Generate all valid architecture configurations
        生成所有有效的架构配置
        行列最小值不能小于2
        """
        valid_configs = []

        for rows in self.row_choices:
            for cols in self.column_choices:
                array_capacity = rows * cols

                # Check if total capacity can be achieved with integer number of arrays
                # 检查是否可以用整数个阵列实现总容量
                if self.total_bits % array_capacity == 0:
                    num_arrays = self.total_bits // array_capacity

                    config = {"rows": rows, "cols": cols, "num_arrays": num_arrays, "array_capacity": array_capacity, "total_capacity": self.total_bits}
                    valid_configs.append(config)

        print(f"Generated {len(valid_configs)} valid configurations (rows in {self.row_choices}, cols in {self.column_choices})")
        print(f"生成了 {len(valid_configs)} 个有效配置 (行={self.row_choices}, 列={self.column_choices})")

        return valid_configs

    def get_configuration(self, index: int) -> Dict:
        """
        Get configuration by index
        根据索引获取配置
        """
        if 0 <= index < len(self.valid_configs):
            return self.valid_configs[index]
        else:
            raise IndexError(f"Configuration index {index} out of range [0, {len(self.valid_configs)-1}]")

    def get_num_configurations(self) -> int:
        """
        Get total number of valid configurations
        获取有效配置的总数
        """
        return len(self.valid_configs)


class JointParameterSpace:
    def __init__(self, arch_space: ArchitectureConfigurationSpace, base_space: ModifiedSRAMParameterSpace):
        self.arch_space = arch_space
        self.base_space = base_space
        self.row_choices = arch_space.row_choices
        self.column_choices = arch_space.column_choices
        prefix = torch.tensor([[0.0, 0.0], [1.0, 1.0]], dtype=torch.float32)
        self.bounds = torch.cat([prefix, base_space.bounds], dim=1)

    def convert_params(self, x):
        if isinstance(x, torch.Tensor):
            if x.dim() > 1:
                x = x.flatten()
        else:
            x = torch.tensor(x, dtype=torch.float32)
        row_idx = int(float(x[0]) * len(self.row_choices))
        col_idx = int(float(x[1]) * len(self.column_choices))
        row_idx = max(0, min(row_idx, len(self.row_choices) - 1))
        col_idx = max(0, min(col_idx, len(self.column_choices) - 1))
        rows = self.row_choices[row_idx]
        cols = self.column_choices[col_idx]
        params = self.base_space.convert_params(x[2:])
        params["rows"] = rows
        params["cols"] = cols
        return params

    def print_params(self, params):
        return self.base_space.print_params(params)


def evaluate_sram_with_config(params, num_rows, num_cols, num_arrays, output_cols=16, timeout=120, *, stage_label="stage_eval", iteration_index=None, temperature=None, corner="TT", gen_unused_cells=True):
    """
    Execute SRAM evaluation with given parameters and specific row-column configuration
    使用给定参数和特定行列配置执行SRAM评估

    This function is copied from demo_joint_optimization.py to make two_stage_optimization.py
    independent of demo_joint_optimization.py
    此函数从demo_joint_optimization.py复制而来，使two_stage_optimization.py不依赖demo_joint_optimization.py
    """
    # 获取项目根目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = current_dir

    # 依据阶段标签确定仿真输出目录：sim/stage1 或 sim/stage2
    sim_subdir = "stage1" if str(stage_label).startswith("stage1") else "stage2" if str(stage_label).startswith("stage2") else str(stage_label)
    if str(stage_label).startswith("joint"):
        stage_parts = str(stage_label).split("/", 1)
        if len(stage_parts) > 1 and stage_parts[1]:
            sim_subdir = str(Path(sim_subdir) / stage_parts[1])
        sim_subdir = str(Path(sim_subdir) / f"r{num_rows}_c{num_cols}_a{num_arrays}")
    # 输出到绝对路径 /OpenYield/size_optimization/sim/<stage>
    sim_dir_path = Path(project_root) / "size_optimization" / "sim" / sim_subdir
    sim_dir_path.mkdir(parents=True, exist_ok=True)

    sram_config = SRAM_CONFIG()
    sram_config.load_all_configs(global_file=os.path.join(project_root, "sram_compiler/config_yaml/global.yaml"), circuit_configs={"SRAM_6T_CELL": os.path.join(project_root, "sram_compiler/config_yaml/sram_6t_cell.yaml"), "WORDLINEDRIVER": os.path.join(project_root, "sram_compiler/config_yaml/wordline_driver.yaml"), "PRECHARGE": os.path.join(project_root, "sram_compiler/config_yaml/precharge.yaml"), "COLUMNMUX": os.path.join(project_root, "sram_compiler/config_yaml/mux.yaml"), "SENSEAMP": os.path.join(project_root, "sram_compiler/config_yaml/sa.yaml"), "WRITEDRIVER": os.path.join(project_root, "sram_compiler/config_yaml/write_driver.yaml"), "DECODER": os.path.join(project_root, "sram_compiler/config_yaml/decoder.yaml")})

    try:
        print(f"Starting SRAM evaluation with {num_rows}x{num_cols} and {output_cols} output config")
        print(f"开始使用{num_rows}x{num_cols},{output_cols}配置进行SRAM评估")

        def _write_and_load_params_csv():
            """将当前参数写入CSV并读取最新一行返回。"""
            # 将参数追踪CSV写入阶段化目录（与网表输出一致）
            sim_dir = sim_dir_path
            sim_dir.mkdir(parents=True, exist_ok=True)

            headers = [
                "timestamp",
                "stage",
                "iteration",
                "rows",
                "cols",
                "pu_width",
                "pd_width",
                "pg_width",
                "length",
                "pmos_model_name",
                "nmos_model_name",
            ]
            timestamp = datetime.now().isoformat(timespec="seconds")
            row = [
                timestamp,
                stage_label,
                "" if iteration_index is None else iteration_index,
                num_rows,
                num_cols,
                params.get("pu_width", 0.0),
                params.get("pd_width", 0.0),
                params.get("pg_width", 0.0),
                params.get("length", 0.0),
                params.get("pmos_model_name", ""),
                params.get("nmos_model_name", ""),
            ]

            history_path = sim_dir / "transistor_params_history.csv"
            write_header = not history_path.exists()
            with open(history_path, "a", newline="", encoding="utf-8") as f_hist:
                writer = csv.writer(f_hist)
                if write_header:
                    writer.writerow(headers)
                writer.writerow(row)

            latest_path = sim_dir / "transistor_params_latest.csv"
            with open(latest_path, "w", newline="", encoding="utf-8") as f_latest:
                writer = csv.writer(f_latest)
                writer.writerow(headers)
                writer.writerow(row)

            with open(latest_path, "r", newline="", encoding="utf-8") as f_latest:
                reader = csv.DictReader(f_latest)
                latest_row = next(reader)

            def _to_float(value):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return value

            return {
                "pu_width": _to_float(latest_row["pu_width"]),
                "pd_width": _to_float(latest_row["pd_width"]),
                "pg_width": _to_float(latest_row["pg_width"]),
                "length": _to_float(latest_row["length"]),
                "pmos_model_name": latest_row["pmos_model_name"],
                "nmos_model_name": latest_row["nmos_model_name"],
            }

        latest_params = _write_and_load_params_csv()
        params.update({k: v for k, v in latest_params.items() if v != ""})

        # CRITICAL: Update the SRAM configuration with the specified row/column counts
        # 关键：使用指定的行列数更新SRAM配置
        sram_config.global_config.num_rows = num_rows
        sram_config.global_config.num_cols = num_cols
        sram_config.global_config.output_cols = output_cols
        if temperature is None:
            temperature = getattr(sram_config.global_config, "temperature", 27)

        # CRITICAL: Update transistor parameters in sram_config before creating testbench
        # 关键：在创建testbench之前更新sram_config中的晶体管参数
        sram_config.sram_6t_cell.pmos_width.value = float(params["pu_width"])
        sram_config.sram_6t_cell.nmos_width.value[0] = float(params["pd_width"])
        sram_config.sram_6t_cell.nmos_width.value[1] = float(params["pg_width"])
        sram_config.sram_6t_cell.length.value = float(params["length"])

        if params.get("pmos_model_name"):
            pmos_model = params["pmos_model_name"]
            if pmos_model in sram_config.sram_6t_cell.pmos_model.choices:
                sram_config.sram_6t_cell.pmos_model.value = pmos_model
            else:
                print(f"Warning: Invalid PMOS model name '{pmos_model}', using default")
                print(f"警告：无效的PMOS模型名称 '{pmos_model}'，使用默认值")

        if params.get("nmos_model_name"):
            nmos_model = params["nmos_model_name"]
            if nmos_model in sram_config.sram_6t_cell.nmos_model.choices:
                sram_config.sram_6t_cell.nmos_model.value[0] = nmos_model
                sram_config.sram_6t_cell.nmos_model.value[1] = nmos_model
            else:
                print(f"Warning: Invalid NMOS model name '{nmos_model}', using default")
                print(f"警告：无效的NMOS模型名称 '{nmos_model}'，使用默认值")

        print(f"Updated SRAM config with parameters: pu={float(params['pu_width'])*1e9:.2f}nm, " f"pd={float(params['pd_width'])*1e9:.2f}nm, pg={float(params['pg_width'])*1e9:.2f}nm, " f"length={float(params['length'])*1e9:.2f}nm")
        print(f"已更新SRAM配置参数: pu={float(params['pu_width'])*1e9:.2f}nm, " f"pd={float(params['pd_width'])*1e9:.2f}nm, pg={float(params['pg_width'])*1e9:.2f}nm, " f"length={float(params['length'])*1e9:.2f}nm")

        start_time = time.time()

        # Set simulation parameters
        # 设置仿真参数
        vdd = 1.0
        pdk_path = os.path.join(project_root, "tran_models/models_TT.spice")
        num_mc = 1

        if not hasattr(evaluate_sram_with_config, "_default_bitcell_area"):
            default_params = get_params_from_yaml()
            evaluate_sram_with_config._default_bitcell_area = estimate_bitcell_area(
                w_access=default_params["pg_width"],
                w_pd=default_params["pd_width"],
                w_pu=default_params["pu_width"],
                l_transistor=default_params["length"],
            )
        base_array_area = estimate_total_area(num_rows, num_cols, num_arrays)
        current_bitcell_area = estimate_bitcell_area(
            w_access=params.get("pg_width", 0.0),
            w_pd=params.get("pd_width", 0.0),
            w_pu=params.get("pu_width", 0.0),
            l_transistor=params.get("length", 0.0),
        )
        default_bitcell_area = getattr(evaluate_sram_with_config, "_default_bitcell_area", 0.0)
        scale_factor = current_bitcell_area / default_bitcell_area if default_bitcell_area > 0 else 1.0
        area = base_array_area * scale_factor

        mc_testbench = Sram6TCoreMcTestbench(
            sram_config,
            w_rc=True,
            pi_res=100 @ u_Ohm,
            pi_cap=0.001 @ u_pF,
            vth_std=0.05,
            use_mc=False,
            custom_mc=False,
            param_sweep=False,
            sweep_precharge=False,
            sweep_senseamp=False,
            sweep_wordlinedriver=False,
            sweep_columnmux=False,
            sweep_writedriver=False,
            sweep_decoder=False,
            coner=corner,
            choose_columnmux=output_cols < num_cols,
            q_init_val=0,
            sim_path=str(sim_dir_path),
            gen_unused_cells=gen_unused_cells,
        )

        

        try:
            # Run simulation directly
            # 直接运行仿真
            if stage_label == "stage1":
                print("Running stage 1 simulation...")
            else:
                print("Running stage 2 simulation...")
                hold_snm = mc_testbench.run_mc_simulation(
                    operation="hold_snm",
                    target_row=num_rows - 1,
                    target_col=num_cols - 1,
                    mc_runs=num_mc,
                    temperature=temperature,
                    vars=None,
                )

                read_snm = mc_testbench.run_mc_simulation(
                    operation="read_snm",
                    target_row=num_rows - 1,
                    target_col=num_cols - 1,
                    mc_runs=num_mc,
                    temperature=temperature,
                    vars=None,
                )

                write_snm = mc_testbench.run_mc_simulation(
                    operation="write_snm",
                    target_row=num_rows - 1,
                    target_col=num_cols - 1,
                    mc_runs=num_mc,
                    temperature=temperature,
                    vars=None,
                )

            w_delay, w_pavg, w_pstc, w_pdyn = mc_testbench.run_mc_simulation(
                operation="write",
                target_row=num_rows - 1,
                target_col=num_cols - 1,
                mc_runs=num_mc,
                temperature=temperature,
                vars=None,
            )

            r_delay, r_pavg, r_pstc, r_pdyn = mc_testbench.run_mc_simulation(
                operation="read",
                target_row=num_rows - 1,
                target_col=num_cols - 1,
                mc_runs=num_mc,
                temperature=temperature,
                vars=None,
            )

            

            # Process simulation results
            # 处理仿真结果
            def get_float_value(sim_result):
                return float(sim_result[0]) if isinstance(sim_result, np.ndarray) else float(sim_result)

            if stage_label == "stage1":
                hold_snm_val = None
                read_snm_val = None
                write_snm_val = None
                min_snm = None
            else:
                hold_snm_val = get_float_value(hold_snm)
                read_snm_val = get_float_value(read_snm)
                write_snm_val = get_float_value(write_snm)
                min_snm = min(hold_snm_val, read_snm_val, write_snm_val)

            # print(w_delay, r_delay)

            # 加上片选信号的延迟
            w_delay += 4.167213500e-11 * np.log2(num_arrays)
            r_delay += 4.167213500e-11 * np.log2(num_arrays)

            # print(w_delay, r_delay)

            # 加上mux的延迟
            mux_delay = 1.8e-10
            r_delay += np.log2(num_arrays) * mux_delay

            # print(w_delay, r_delay)

            # exit(0)

            read_power = get_float_value(r_pstc) * num_arrays + get_float_value(r_pdyn)
            write_power = get_float_value(w_pstc) * num_arrays + get_float_value(w_pdyn)

            # 加上mux的功耗
            mux_power = 0.1e-6
            read_power -= (num_arrays - 1) * np.log2(num_arrays) * mux_power

            if num_cols < output_cols:
                # 需要多个回合
                w_delay *= output_cols // num_cols
                r_delay *= output_cols // num_cols

                read_power += get_float_value(r_pdyn) * (output_cols // num_cols)
                write_power += get_float_value(r_pdyn) * (output_cols // num_cols)

            # Take absolute value of power
            # 取功耗的绝对值
            read_power = abs(read_power)
            write_power = abs(write_power)
            max_power = max(read_power, write_power)

            read_delay = float(r_delay[0]) if isinstance(r_delay, np.ndarray) else float(r_delay)
            write_delay = float(w_delay[0]) if isinstance(w_delay, np.ndarray) else float(w_delay)

            # If any delay equals -1, treat this evaluation as invalid and discard the solution
            # 如果任一延迟为 -1，则视为无效评估并舍弃该解
            if (read_delay == -1) or (write_delay == -1):
                print("Invalid delay detected (read/write = -1). Discarding this solution.")
                print("检测到无效延迟（读/写为 -1）。舍弃该解。")
                objectives = [0.01, -1e-3, -1e-10]  # Penalty objective function
                constraints = [1.0, 1.0]  # Constraint violation
                return objectives, constraints, None, False

            read_delay_feasible = True
            write_delay_feasible = True

            # Calculate FoM (Figure of Merit)
            # 计算FoM（品质因数）
            # Stage 1: FoM = log10(1 / (max_power * sqrt(area) * max_delay))
            # 阶段1: FoM = log10(1 / (max_power * sqrt(area) * max_delay))
            # Stage 2: FoM = log10(min_snm / (max_power * max_delay))
            # 阶段2: FoM = log10(min_snm / (max_power * max_delay))
            max_delay = max(read_delay, write_delay)
            if stage_label == "stage1":
                if max_power > 0 and area > 0 and max_delay > 0:
                    fom = np.log10(1 / (max_power * np.sqrt(area) * max_delay))
                else:
                    fom = -10.0  # Penalty value for invalid cases

                # Construct objectives (for multi-objective optimization)
                # 构建目标函数（用于多目标优化）
                objectives = [-max_power, -area]  # Maximize SNM, minimize power and area

            else:
                # Stage 2 FoM no longer includes area; uses min_snm numerator
                # 阶段2 FoM 不再包含面积项；使用 min_snm 作为分子
                if min_snm > 0 and max_power > 0 and max_delay > 0:
                    fom = np.log10(min_snm / (max_power * max_delay))
                else:
                    fom = -10.0  # Penalty value for invalid cases

                # Construct objectives (for multi-objective optimization)
                # 构建目标函数（用于多目标优化）
                # Stage 2 objectives aligned with FoM: maximize min_snm, minimize power and delay
                # 阶段2目标与FoM一致：最大化 min_snm，最小化功耗与延迟
                objectives = [min_snm, -max_power, -max_delay]

            # Construct detailed results
            # 构建详细结果
            result = {"hold_snm": hold_snm_val, "read_snm": read_snm_val, "write_snm": write_snm_val, "min_snm": min_snm, "read_power": read_power, "write_power": write_power, "max_power": max_power, "read_delay": read_delay, "write_delay": write_delay, "max_delay": max_delay, "area": area, "fom": fom, "read_delay_feasible": read_delay_feasible, "write_delay_feasible": write_delay_feasible}

            # 补充阵列规模信息，供外部保存
            result.update(
                {
                    "num_rows": num_rows,
                    "num_cols": num_cols,
                    "capacity": num_rows * num_cols,
                    "aspect_ratio": (num_rows / num_cols) if num_cols else None,
                }
            )

            end_time = time.time()
            print(f"Simulation completed successfully! Time taken: {end_time - start_time:.2f} seconds")
            print(f"仿真成功完成！用时: {end_time - start_time:.2f} 秒")

            constraints = [0, 0]  # Constraint violation

            return objectives, constraints, result, True

        

        except Exception as e:
            print(f"Error occurred during simulation: {str(e)}")
            print(f"仿真过程中发生错误: {str(e)}")
            traceback.print_exc()
            objectives = [0.01, -1e-3, -1e-10]  # Penalty objective function
            constraints = [1.0, 1.0]  # Constraint violation
            return objectives, constraints, None, False

    except Exception as e:
        print(f"Error in testbench setup: {str(e)}")
        print(f"测试平台设置错误: {str(e)}")
        traceback.print_exc()
        objectives = [0.01, -1e-3, -1e-10]  # Penalty objective function
        constraints = [1.0, 1.0]  # Constraint violation
        return objectives, constraints, None, False


class SAOptimizer:
    """
    Simulated Annealing Optimizer
    模拟退火优化器
    """

    def __init__(self, evaluation_function, bounds=None, maximize=True):
        """
        Initialize SA optimizer
        初始化SA优化器

        Args:
            evaluation_function: Function to evaluate solutions
            bounds: Parameter bounds (for continuous optimization)
            maximize: Whether to maximize (True) or minimize (False) the objective
        """
        self.evaluation_function = evaluation_function
        self.bounds = bounds
        self.maximize = maximize
        self.best_solution = None
        self.best_value = float("-inf") if maximize else float("inf")
        self.history = []

    def _accept_probability(self, old_value, new_value, temperature):
        """
        Calculate acceptance probability for SA
        计算SA的接受概率
        """
        if self.maximize:
            if new_value > old_value:
                return 1.0
            else:
                return np.exp((new_value - old_value) / temperature)
        else:
            if new_value < old_value:
                return 1.0
            else:
                return np.exp((old_value - new_value) / temperature)

    def optimize_discrete(self, num_solutions, max_iter=100, T_max=1000, T_min=1e-7):
        """
        Optimize discrete solution space (for Stage 1)
        优化离散解空间（用于第一阶段）
        """
        print(f"Starting SA optimization for discrete space with {num_solutions} solutions")
        print(f"开始对包含{num_solutions}个解的离散空间进行SA优化")

        # Initialize with random solution
        current_solution = random.randint(0, num_solutions - 1)
        current_value, current_result = self.evaluation_function(current_solution)

        # Track best solution
        self.best_solution = current_solution
        self.best_value = current_value
        self.best_result = current_result

        # Temperature schedule
        T = T_max
        alpha = (T_min / T_max) ** (1.0 / max_iter)

        print(f"Initial solution: {current_solution}, value: {current_value:.6f}")
        print(f"初始解: {current_solution}, 值: {current_value:.6f}")

        for iteration in range(max_iter):
            # Generate neighbor solution
            neighbor_solution = random.randint(0, num_solutions - 1)
            neighbor_value, neighbor_result = self.evaluation_function(neighbor_solution)

            # Accept or reject
            accept_prob = self._accept_probability(current_value, neighbor_value, T)
            random_val = random.random()
            accepted = random_val < accept_prob

            if accepted:
                current_solution = neighbor_solution
                current_value = neighbor_value
                current_result = neighbor_result

                # Update best solution
                if (self.maximize and current_value > self.best_value) or (not self.maximize and current_value < self.best_value):
                    self.best_solution = current_solution
                    self.best_value = current_value
                    self.best_result = current_result
                    print(f"Iteration {iteration}: New best solution {self.best_solution}, value: {self.best_value:.6f}")
                    print(f"迭代 {iteration}: 新的最佳解 {self.best_solution}, 值: {self.best_value:.6f}")

            # Record history
            self.history.append({"iteration": iteration, "current_solution": current_solution, "current_value": current_value, "best_value": self.best_value, "temperature": T, "accepted": accepted})

            # Cool down
            T *= alpha

            if iteration % 10 == 0:
                print(f"Iteration {iteration}: T={T:.2e}, current_value={current_value:.6f}, best_value={self.best_value:.6f}")
                print(f"迭代 {iteration}: T={T:.2e}, 当前值={current_value:.6f}, 最佳值={self.best_value:.6f}")

        return self.best_solution, self.best_value, self.best_result

    def optimize_continuous(self, initial_solution, max_iter=100, T_max=1000, T_min=1e-7):
        """
        Optimize continuous solution space (for Stage 2)
        优化连续解空间（用于第二阶段）
        """
        print(f"Starting SA optimization for continuous space")
        print(f"开始连续空间的SA优化")

        # Initialize
        current_solution = np.array(initial_solution)
        current_value, current_result = self.evaluation_function(current_solution)

        # Track best solution
        self.best_solution = current_solution.copy()
        self.best_value = current_value
        self.best_result = current_result

        # Temperature schedule
        T = T_max
        alpha = (T_min / T_max) ** (1.0 / max_iter)

        print(f"Initial value: {current_value:.6f}")
        print(f"初始值: {current_value:.6f}")

        for iteration in range(max_iter):
            # Generate neighbor solution
            neighbor_solution = current_solution + np.random.normal(0, 0.1, size=current_solution.shape)

            # Apply bounds if specified
            if self.bounds is not None:
                neighbor_solution = np.clip(neighbor_solution, self.bounds[0], self.bounds[1])

            neighbor_value, neighbor_result = self.evaluation_function(neighbor_solution)

            # Accept or reject
            accept_prob = self._accept_probability(current_value, neighbor_value, T)
            random_val = random.random()
            accepted = random_val < accept_prob

            if accepted:
                current_solution = neighbor_solution.copy()
                current_value = neighbor_value
                current_result = neighbor_result

                # Update best solution
                if (self.maximize and current_value > self.best_value) or (not self.maximize and current_value < self.best_value):
                    self.best_solution = current_solution.copy()
                    self.best_value = current_value
                    self.best_result = current_result
                    print(f"Iteration {iteration}: New best value: {self.best_value:.6f}")
                    print(f"迭代 {iteration}: 新的最佳值: {self.best_value:.6f}")

            # Record history
            self.history.append({"iteration": iteration, "current_value": current_value, "best_value": self.best_value, "temperature": T, "accepted": accepted})

            # Cool down
            T *= alpha

            if iteration % 10 == 0:
                print(f"Iteration {iteration}: T={T:.2e}, current_value={current_value:.6f}, best_value={self.best_value:.6f}")
                print(f"迭代 {iteration}: T={T:.2e}, 当前值={current_value:.6f}, 最佳值={self.best_value:.6f}")

        return self.best_solution, self.best_value, self.best_result


class SMACStage1Optimizer:
    """
    SMAC optimizer for Stage 1 discrete optimization (architecture configuration)
    阶段1离散优化（架构配置）的SMAC优化器
    """

    def __init__(self, evaluation_function, num_configurations, maximize=True):
        """
        Initialize SMAC optimizer for discrete space
        初始化离散空间的SMAC优化器

        Args:
            evaluation_function: Function to evaluate configuration index -> (fom, result)
            num_configurations: Total number of valid configurations
            maximize: Whether to maximize (True) or minimize (False) the objective
        """
        if not SMAC_AVAILABLE:
            raise ImportError("SMAC is not available. Please install with: pip install smac ConfigSpace")

        self.evaluation_function = evaluation_function
        self.num_configurations = num_configurations
        self.maximize = maximize
        self.best_solution = None
        self.best_value = float("-inf") if maximize else float("inf")
        self.best_result = None
        self.history = []
        self.evaluation_count = 0

        # Create configuration space with single integer hyperparameter
        # 创建包含单个整数超参数的配置空间
        self.cs = ConfigurationSpace()
        # Use UniformIntegerHyperparameter with positional arguments
        # 使用UniformIntegerHyperparameter，参数为位置参数
        hp = CSH.UniformIntegerHyperparameter("config_index", 0, num_configurations - 1, default_value=num_configurations // 2)  # lower bound  # upper bound
        self.cs.add_hyperparameter(hp)

    def smac_objective(self, config: Configuration, seed: int = 0) -> float:
        """
        Objective function for SMAC (discrete optimization)
        SMAC的目标函数（离散优化）
        """
        # Extract configuration index
        # 提取配置索引
        config_index = config["config_index"]
        config_index = int(config_index)

        # Ensure index is within valid range
        # 确保索引在有效范围内
        config_index = max(0, min(config_index, self.num_configurations - 1))

        print(f"\n===== SMAC Stage 1 评估 {self.evaluation_count + 1} =====")
        print(f"评估配置索引: {config_index}/{self.num_configurations - 1}")

        # Evaluate configuration
        # 评估配置
        start_time = time.time()
        fom, result = self.evaluation_function(config_index)
        end_time = time.time()

        print(f"评估用时: {end_time - start_time:.2f} 秒")
        print(f"FoM: {fom:.6e}")

        # Record history
        # 记录历史
        self.history.append({"iteration": self.evaluation_count, "config_index": config_index, "fom": fom, "result": result})

        # Update best solution
        # 更新最佳解
        if (self.maximize and fom > self.best_value) or (not self.maximize and fom < self.best_value):
            self.best_solution = config_index
            self.best_value = fom
            self.best_result = result
            print(f"*** 发现新的最优解: 索引={config_index}, FoM={fom:.6e} ***")

        self.evaluation_count += 1

        # SMAC minimizes, so return negative FoM if maximizing
        # SMAC是最小化，所以如果最大化则返回负FoM
        if self.maximize:
            return -fom
        else:
            return fom

    def optimize_discrete(self, max_iter=100):
        """
        Run SMAC optimization for discrete space
        运行离散空间的SMAC优化
        """
        print(f"Starting SMAC optimization for discrete space with {self.num_configurations} configurations")
        print(f"开始对包含{self.num_configurations}个配置的离散空间进行SMAC优化")

        # Create SMAC scenario
        # 创建SMAC场景
        scenario = Scenario(
            configspace=self.cs,
            deterministic=True,
            n_trials=max_iter,
            seed=42,
        )

        # Initialize SMAC
        # 初始化SMAC
        smac = HyperparameterOptimizationFacade(
            scenario,
            self.smac_objective,
            dask_client=None,  # No parallel execution
        )

        # Run optimization
        # 运行优化
        print("开始SMAC优化循环...")
        incumbent = smac.optimize()

        # Extract best configuration index
        # 提取最佳配置索引
        best_config_index = int(incumbent["config_index"])
        best_config_index = max(0, min(best_config_index, self.num_configurations - 1))

        print(f"\nSMAC优化完成，共进行{self.evaluation_count}次评估")
        print(f"最终配置索引: {best_config_index}")

        # Use best solution found during optimization
        # 使用优化过程中找到的最佳解
        if self.best_solution is not None:
            return self.best_solution, self.best_value, self.best_result
        else:
            # Fallback: evaluate the incumbent configuration
            # 后备方案：评估最终配置
            fom, result = self.evaluation_function(best_config_index)
            return best_config_index, fom, result


class TwoStageOptimizer:
    """
    Joint SRAM optimization
    SRAM联合优化
    """

    def __init__(self, seed=42, gen_unused_cells=True):
        """
        Initialize two-stage optimizer
        初始化二阶段优化器
        """
        # Set random seed
        seed_set(seed)
        self.seed = seed

        # Create directories
        create_directories()

        self.gen_unused_cells = gen_unused_cells

        # Initialize architecture configuration space
        self.arch_space = ArchitectureConfigurationSpace()

        # Initialize transistor parameter space
        self.param_space = ModifiedSRAMParameterSpace()

        # Results storage
        self.joint_results = {}

        # Iteration history storage
        # 迭代历史存储
        self.joint_iteration_history = []
        self.joint_csv_tag = None

        print("Joint optimizer initialized")
        print("联合优化器已初始化")

    def _append_iteration_csv(self, stage: str, record: Dict[str, Any], label: str = None):
        algorithm_dir = getattr(self, "current_algorithm", None) or "unknown"
        base_dir = Path(project_root) / "size_optimization" / "experiment" / algorithm_dir
        base_dir.mkdir(parents=True, exist_ok=True)
        if label == "joint" and self.joint_csv_tag:
            filename = f"{stage}_iterations_live_joint_{self.joint_csv_tag}.csv"
        else:
            filename = f"{stage}_iterations_live.csv" if not label else f"{stage}_iterations_live_{label}.csv"
        path = base_dir / filename

        stage2_fields = [
            "iteration",
            "fom",
            "success",
            "rows",
            "cols",
            "num_arrays",
            "pg_width",
            "pd_width",
            "pu_width",
            "length",
            "nmos_model_name",
            "pmos_model_name",
            "min_snm",
            "hold_snm",
            "read_snm",
            "write_snm",
            "read_delay",
            "write_delay",
            "max_delay",
            "read_power",
            "write_power",
            "max_power",
            "total_power",
            "single_array_area",
            "total_area",
            "objective_0",
            "objective_1",
            "objective_2",
            "constraint_0",
            "constraint_1",
        ]

        fields = stage2_fields
        write_header = not path.exists()
        if not record.get("success", False):
            return
        key_fields = ["pg_width", "pd_width", "pu_width", "length", "nmos_model_name", "pmos_model_name", "fom", "max_delay", "max_power"]
        last = None
        if path.exists():
            try:
                with open(path, "r", newline="", encoding="utf-8") as fr:
                    reader = csv.DictReader(fr)
                    for r in reader:
                        last = r
            except Exception:
                last = None
        dedupe = False
        if last is not None:
            try:
                dedupe = all(str(record.get(k, "")) == str(last.get(k, "")) for k in key_fields if k in fields)
            except Exception:
                dedupe = False
        if dedupe:
            return
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            if write_header:
                writer.writeheader()
            row = {k: record.get(k, "") for k in fields}
            writer.writerow(row)

    def _calculate_timeout(self, rows, cols, base_timeout=120):
        """
        Calculate dynamic timeout based on configuration size
        根据配置大小计算动态超时时间

        Args:
            rows: Number of rows
            cols: Number of columns
            base_timeout: Base timeout in seconds (default 120)

        Returns:
            Calculated timeout in seconds
        """
        # Calculate array size
        # 计算阵列大小
        array_size = rows * cols

        # Timeout scales with array size
        # For small arrays (< 1000 bits): use base timeout
        # For medium arrays (1000-10000 bits): scale by 1.5x
        # For large arrays (> 10000 bits): scale by 2.0x or more
        # 超时时间随阵列大小缩放
        # 小阵列 (< 1000 bits): 使用基础超时
        # 中等阵列 (1000-10000 bits): 缩放1.5倍
        # 大阵列 (> 10000 bits): 缩放2.0倍或更多

        if array_size < 1000:
            timeout = base_timeout
        elif array_size < 10000:
            # Linear scaling: 1.0 to 1.5x
            # 线性缩放：1.0到1.5倍
            scale = 1.0 + 0.5 * (array_size - 1000) / 9000
            timeout = int(base_timeout * scale)
        else:
            # For very large arrays, use more aggressive scaling
            # 对于非常大的阵列，使用更激进的缩放
            # Scale factor: 1.5 + (size - 10000) / 20000, capped at 3.0x
            # 缩放因子：1.5 + (大小 - 10000) / 20000，上限为3.0倍
            scale = min(1.5 + (array_size - 10000) / 20000, 3.0)
            timeout = int(base_timeout * scale)

        # Ensure minimum timeout
        # 确保最小超时时间
        timeout = max(timeout, base_timeout)

        return timeout

    def _decode_joint_vector(self, x):
        x = np.array(x, dtype=float)
        if x.size < 2:
            return None
        row_count = len(self.arch_space.row_choices)
        col_count = len(self.arch_space.column_choices)
        row_idx = int(x[0] * row_count)
        col_idx = int(x[1] * col_count)
        row_idx = max(0, min(row_idx, row_count - 1))
        col_idx = max(0, min(col_idx, col_count - 1))
        rows = self.arch_space.row_choices[row_idx]
        cols = self.arch_space.column_choices[col_idx]
        array_capacity = rows * cols
        if self.arch_space.total_bits % array_capacity != 0:
            return None
        num_arrays = self.arch_space.total_bits // array_capacity
        params_tensor = torch.tensor(x[2:], dtype=torch.float32)
        params = self.param_space.convert_params(params_tensor)
        return rows, cols, num_arrays, params, array_capacity, row_idx, col_idx

    def run_joint_optimization(self, max_iter=200, algorithm="SA"):
        print("=" * 60)
        print("JOINT SRAM OPTIMIZATION")
        print("架构与晶体管尺寸联合优化")
        print("=" * 60)

        self.current_algorithm = algorithm
        seed_offsets = {"SA": 1, "PSO": 2, "SMAC": 3, "CBO": 4, "RoSE_Opt": 5, "MOEAD": 6}
        seed_set(self.seed + seed_offsets.get(algorithm, 0))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.joint_csv_tag = f"{algorithm}_{max_iter}_{timestamp}"
        self.joint_iteration_history = []
        iteration_counter = {"count": 0}
        joint_param_space = JointParameterSpace(self.arch_space, self.param_space)

        def _evaluate_joint(x):
            decoded = None
            params = None
            if isinstance(x, dict):
                params = dict(x)
                rows = params.get("rows", self.arch_space.row_choices[0])
                cols = params.get("cols", self.arch_space.column_choices[0])
                array_capacity = rows * cols
                if self.arch_space.total_bits % array_capacity == 0:
                    num_arrays = self.arch_space.total_bits // array_capacity
                    decoded = (rows, cols, num_arrays, params, array_capacity, None, None)
            else:
                decoded = self._decode_joint_vector(x)
            iteration_num = iteration_counter["count"]
            iteration_counter["count"] += 1
            if decoded is None:
                record = {"iteration": iteration_num, "fom": -1e9, "success": False}
                self.joint_iteration_history.append(record)
                self._append_iteration_csv("stage2", record, label="joint")
                return -1e9, None, None, None, False, None, params

            rows, cols, num_arrays, params, array_capacity, row_idx, col_idx = decoded
            timeout = self._calculate_timeout(rows, cols)
            objectives, constraints, result, success = evaluate_sram_with_config(
                params,
                rows,
                cols,
                num_arrays,
                timeout=timeout,
                stage_label=f"joint/{algorithm}",
                iteration_index=iteration_num,
                gen_unused_cells=self.gen_unused_cells,
            )
            fom = -1e9
            if success and result:
                total_power = result["max_power"]
                max_delay = max(result["read_delay"], result["write_delay"])
                area = result.get("area", 0)
                if result["min_snm"] > 0 and total_power > 0 and area > 0 and max_delay > 0:
                    fom = np.log10(result["min_snm"] / (total_power * np.sqrt(area) * max_delay))
                else:
                    fom = -10.0
                result["total_power"] = total_power
                result["total_area"] = area
                result["fom"] = fom
                result["merit"] = fom
                result["num_rows"] = rows
                result["num_cols"] = cols
                result["num_arrays"] = num_arrays

            record = {
                "iteration": iteration_num,
                "fom": fom if fom is not None else -1e9,
                "success": success,
                "rows": rows,
                "cols": cols,
                "num_arrays": num_arrays,
                "pg_width": params.get("pg_width", 0),
                "pd_width": params.get("pd_width", 0),
                "pu_width": params.get("pu_width", 0),
                "length": params.get("length", 0),
                "nmos_model_name": params.get("nmos_model_name", ""),
                "pmos_model_name": params.get("pmos_model_name", ""),
            }
            if success and result:
                record.update(
                    {
                        "min_snm": result.get("min_snm", 0),
                        "hold_snm": result.get("hold_snm", 0),
                        "read_snm": result.get("read_snm", 0),
                        "write_snm": result.get("write_snm", 0),
                        "read_delay": result.get("read_delay", 0),
                        "write_delay": result.get("write_delay", 0),
                        "max_delay": max(result.get("read_delay", 0), result.get("write_delay", 0)),
                        "read_power": result.get("read_power", 0),
                        "write_power": result.get("write_power", 0),
                        "max_power": result.get("max_power", 0),
                        "total_power": result.get("total_power", 0),
                        "single_array_area": result.get("area", 0),
                        "total_area": result.get("total_area", 0),
                    }
                )
            if objectives:
                record["objective_0"] = objectives[0] if len(objectives) > 0 else 0
                record["objective_1"] = objectives[1] if len(objectives) > 1 else 0
                record["objective_2"] = objectives[2] if len(objectives) > 2 else 0
            if constraints:
                record["constraint_0"] = constraints[0] if len(constraints) > 0 else 0
                record["constraint_1"] = constraints[1] if len(constraints) > 1 else 0

            self.joint_iteration_history.append(record)
            self._append_iteration_csv("stage2", record, label="joint")

            config = {"rows": rows, "cols": cols, "num_arrays": num_arrays, "array_capacity": array_capacity}
            return fom, objectives, constraints, result, success, config, params

        def joint_eval_fn(x):
            fom, objectives, constraints, result, success, config, params = _evaluate_joint(x)
            return fom, {"config": config, "params": params, "result": result, "success": success}

        def joint_eval_backend(x):
            fom, objectives, constraints, result, success, config, params = _evaluate_joint(x)
            if objectives is None:
                objectives = [fom, 0.0, 0.0]
            if constraints is None:
                constraints = [1.0, 1.0]
            if success and result:
                if "merit" not in result:
                    result["merit"] = fom
                if "fom" not in result:
                    result["fom"] = fom
            return objectives, constraints, result, success

        if algorithm == "SA":
            param_dim = int(self.param_space.bounds.shape[1])
            total_dim = param_dim + 2
            bounds = (np.zeros(total_dim), np.ones(total_dim))
            initial_solution = np.random.rand(total_dim)
            if total_dim >= 2:
                initial_solution[0] = 0.0
                initial_solution[1] = 0.0

            sa_optimizer = SAOptimizer(evaluation_function=joint_eval_fn, bounds=bounds, maximize=True)
            best_solution, best_fom, best_result = sa_optimizer.optimize_continuous(initial_solution, max_iter=max_iter)

            best_config = None
            best_params = None
            decoded_best = self._decode_joint_vector(best_solution)
            if decoded_best is not None:
                rows, cols, num_arrays, params, array_capacity, row_idx, col_idx = decoded_best
                best_config = {"rows": rows, "cols": cols, "num_arrays": num_arrays, "array_capacity": array_capacity}
                best_params = params

            self.joint_results = {
                "best_config": best_config,
                "best_params": best_params,
                "best_fom": best_fom,
                "best_result": best_result,
                "history": sa_optimizer.history,
                "algorithm": algorithm,
            }
            return self.joint_results

        problem = (joint_param_space, joint_eval_backend, None)
        ret = None
        if algorithm == "PSO":
            from size_optimization import demo_pso

            ret = demo_pso.main("config_sram.yaml", problem=problem, max_iter=max_iter)
        elif algorithm == "SMAC":
            from size_optimization import demo_smac

            ret = demo_smac.main("config_sram.yaml", problem=problem, max_iter=max_iter)
        elif algorithm == "CBO":
            from size_optimization import demo_cbo

            ret = demo_cbo.main("config_sram.yaml", problem=problem, max_iter=max_iter)
        elif algorithm == "RoSE_Opt":
            from size_optimization import demo_roseopt

            ret = demo_roseopt.main("config_sram.yaml", problem=problem, max_iter=max_iter)
        elif algorithm == "MOEAD":
            from size_optimization import demo_moead

            circuit_mode = 1 if self.gen_unused_cells else 2
            ret = demo_moead.main("config_sram.yaml", problem=problem, max_iter=max_iter, circuit_mode=circuit_mode)
        elif algorithm == "MOBO":
            from size_optimization import demo_mobo

            circuit_mode = 1 if self.gen_unused_cells else 2
            ret = demo_mobo.main("config_sram.yaml", problem=problem, max_iter=max_iter, circuit_mode=circuit_mode)
        elif algorithm == "NSGA-II":
            from size_optimization import demo_nsgaii

            circuit_mode = 1 if self.gen_unused_cells else 2
            ret = demo_nsgaii.main("config_sram.yaml", problem=problem, max_iter=max_iter, circuit_mode=circuit_mode)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")

        best_params = ret.get("params") if isinstance(ret, dict) else None
        best_result = ret.get("result") if isinstance(ret, dict) else None
        best_fom = ret.get("merit") if isinstance(ret, dict) else None
        best_config = None
        if isinstance(best_params, dict) and ("rows" in best_params) and ("cols" in best_params):
            rows = best_params["rows"]
            cols = best_params["cols"]
            array_capacity = rows * cols
            if self.arch_space.total_bits % array_capacity == 0:
                num_arrays = self.arch_space.total_bits // array_capacity
                best_config = {"rows": rows, "cols": cols, "num_arrays": num_arrays, "array_capacity": array_capacity}

        self.joint_results = {
            "best_config": best_config,
            "best_params": best_params,
            "best_fom": best_fom,
            "best_result": best_result,
            "algorithm": algorithm,
        }
        return self.joint_results

    def _convert_for_json(self, obj):
        """
        Convert numpy arrays and other non-serializable objects for JSON
        为JSON转换numpy数组和其他不可序列化对象
        """
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_for_json(item) for item in obj]
        else:
            return obj

    def _print_summary(self, results):
        """
        Print optimization summary
        打印优化总结
        """
        print("\n" + "=" * 80)
        print("TWO-STAGE OPTIMIZATION SUMMARY")
        print("二阶段优化总结")
        print("=" * 80)

    def _compute_pareto_frontier(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        计算二维点集（功耗-延时）的极小帕累托前沿。
        参数点为 (power, delay)，均越小越优。
        返回按 power 升序排序的前沿点集。
        """
        if not points:
            return []
        # 去重并按功耗升序、延时升序排序
        unique = list({(float(p), float(d)) for p, d in points})
        sorted_pts = sorted(unique, key=lambda x: (x[0], x[1]))
        frontier: List[Tuple[float, float]] = []
        min_delay = float("inf")
        for pwr, dly in sorted_pts:
            if dly <= min_delay:
                frontier.append((pwr, dly))
                min_delay = dly
        return frontier

    def _plot_power_delay_pareto_stage1(self, output_png_path: str):
        """
        绘制阶段1（架构优化）的功耗-延时散点与帕累托前沿，并保存到指定路径。
        目标函数参考：FOM = log10(1/ (max_power * sqrt(total_area) * max_delay))（最大化）。
        此处帕累托前沿按功耗与延时的极小解计算。
        """
        try:
            # 从迭代历史中提取有效数据
            points: List[Tuple[float, float]] = []
            for rec in getattr(self, "stage1_iteration_history", []):
                if rec.get("success") and ("total_power" in rec) and ("max_delay" in rec):
                    try:
                        pwr = float(rec["total_power"])
                        dly = float(rec["max_delay"])
                    except Exception:
                        continue
                    if pwr > 0 and dly > 0:
                        points.append((pwr, dly))

            if not points:
                print("No valid Stage 1 points to plot Pareto frontier.")
                return

            frontier = self._compute_pareto_frontier(points)

            # 绘图
            plt.figure(figsize=(8, 6))
            p_all = [p for p, d in points]
            d_all = [d for p, d in points]
            plt.scatter(p_all, d_all, s=24, c="tab:blue", alpha=0.6, label="All configs")

            if frontier:
                p_f = [p for p, d in frontier]
                d_f = [d for p, d in frontier]
                plt.plot(p_f, d_f, "-o", color="tab:red", linewidth=2, markersize=4, label="Pareto frontier")

            plt.xlabel("Total Power (W)")
            plt.ylabel("Max Delay (s)")
            plt.title("Stage 1 Power-Delay Pareto Frontier")
            plt.grid(True, alpha=0.3)
            plt.legend(loc="best")
            plt.tight_layout()

            out_path = Path(output_png_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(out_path), dpi=200)
            plt.close()
            print(f"Stage 1 Pareto plot saved: {out_path}")
        except Exception as e:
            print(f"Error while plotting Stage 1 Pareto frontier: {e}")


def main():
    """
    Main function to run two-stage optimization
    运行二阶段优化的主函数
    """
    print("\n" + "=" * 60)
    print("Two-Stage SRAM Optimization")
    print("二阶段SRAM优化")
    print("=" * 60)

    circuit_mode_raw = input("Select circuit mode (1=real, 2=equivalent, default=1): ").strip()
    try:
        circuit_mode = int(circuit_mode_raw) if circuit_mode_raw else 1
        if circuit_mode not in (1, 2):
            raise ValueError
    except Exception:
        circuit_mode = 1
        print("Invalid input. Default to 1.")
    gen_unused_cells = circuit_mode == 1
    if gen_unused_cells:
        print("Using real 6T cell + peripheral circuits.")
    else:
        print("Using equivalent 6T cell + peripheral circuits.")

    max_iter_input = input("Enter the maximum number of iterations for joint optimization (default=40): ").strip()
    try:
        max_iter = int(max_iter_input) if max_iter_input else 40
    except ValueError:
        max_iter = 40
        print("Invalid input. Default to 40.")

    print(f"Maximum number of iterations for joint optimization: {max_iter}")

    algorithm_raw = input("Select algorithm for joint optimization (1=SA, 2=PSO, 3=SMAC, 4=CBO, 5=RoSE_Opt, 6=MOEAD, 7=MOBO, 8=NSGA-II, default=1): ").strip()
    algorithm_norm = algorithm_raw.replace("-", "_").strip()
    algorithm_map = {"1": "SA", "2": "PSO", "3": "SMAC", "4": "CBO", "5": "RoSE_Opt", "6": "MOEAD", "7": "MOBO", "8": "NSGA-II"}
    if not algorithm_norm:
        algorithm = "SA"
    elif algorithm_norm in algorithm_map:
        algorithm = algorithm_map[algorithm_norm]
    else:
        upper = algorithm_norm.upper()
        if upper in {"SA", "PSO", "SMAC", "CBO"}:
            algorithm = upper
        elif upper in {"ROSE_OPT", "ROSEOPT"}:
            algorithm = "RoSE_Opt"
        elif upper in {"MOEAD"}:
            algorithm = "MOEAD"
        elif upper in {"MOBO"}:
            algorithm = "MOBO"
        elif upper in {"NSGA_II", "NSGAII", "NSGA-II"}:
            algorithm = "NSGA-II"
        else:
            algorithm = "SA"
            print("Invalid algorithm input. Default to SA.")

    print(f"Joint optimization algorithm: {algorithm}")

    optimizer = TwoStageOptimizer(seed=42, gen_unused_cells=gen_unused_cells)

    results = optimizer.run_joint_optimization(max_iter=max_iter, algorithm=algorithm)

    return results


if __name__ == "__main__":
    main()
