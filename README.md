# **OpenOpt: An Open-Source SRAM Optimizer Based on Equivalent Circuit Model**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PDK](https://img.shields.io/badge/PDK-FreePDK45-orange.svg)

This repository contains the implementation of:

**OpenOpt: An Open-Source SRAM Architecture and Sizing Co-Optimization Framework Based on Equivalent Circuit Model**

OpenOpt addresses the PPA (Power, Performance, Area) trade-off challenges and large-scale array SPICE simulation efficiency bottlenecks in SRAM design. It provides a comprehensive co-optimization platform that jointly searches architecture parameters (row/column counts, array counts) and transistor-level sizing within a unified design space.

---

## 📌 Overview

As semiconductor process nodes continue to scale down, SRAM design faces two major bottlenecks:

1. **Simulation Efficiency**: Full-array SPICE simulation runtime grows exponentially with array size, making iterative optimization prohibitive for large-scale SRAM arrays.

2. **Joint Optimization**: SRAM performance depends on both architecture configuration and transistor sizing. Traditional methods separate these aspects, making it difficult to find globally optimal solutions.

OpenOpt addresses these challenges through:

- **Equivalent Circuit Model**: Simplifies inactive SRAM cells into equivalent RC loads and static power models, achieving up to **61.4× simulation speedup** while maintaining high fidelity (read/write delay error <0.22%, power error <1.68%)

- **Architecture-Sizing Co-optimization**: Joint search space covering row/column counts, array counts, transistor W/L, and threshold types

- **Multiple Optimization Algorithms**: SA, PSO, CBO, SMAC, RoSE-Opt, NSGA-II, MOEA/D, and Random

---

## ✨ Highlights

### ✔️ Equivalent Circuit Model for Simulation Acceleration

- **BL/BLB Terminal Model**: Capacitor-to-ground equivalent for inactive cells
- **WL Terminal Model**: Simplified capacitance model capturing piecewise behavior
- **Static Power Model**: Large resistance from VDD to ground
- **Linear Scalability**: Computational complexity decoupled from array size
- **High Fidelity**: <0.22% delay error, <1.68% power error across all tested scales (up to 512×512)

### ✔️ Complete 6T SRAM Simulation Framework

- Full SRAM array with configurable rows and columns
- All peripheral circuits (WL driver, precharge, SA, write driver, decoder, mux)
- Process corner support (TT/FF/SS/FS/SF)
- Monte Carlo variation analysis with configurable Vth standard deviation
- RC parasitic modeling with π-network

### ✔️ Architecture-Sizing Co-optimization

| Level | Parameters | Description |
|-------|------------|-------------|
| Architecture | num_rows, num_cols | Array dimensions |
| Architecture | num_arrays | Number of arrays under capacity constraint |
| Transistor | W_PD, W_PU, W_PG | Transistor widths |
| Transistor | L | Channel length |
| Transistor | nmos_model_name, pmos_model_name | Threshold model selection |

### ✔️ Rich Algorithm Library

| Algorithm | Type | Description |
|-----------|------|-------------|
| SA | Single-objective | Simulated Annealing with exponential cooling |
| PSO | Single-objective | Particle Swarm Optimization |
| CBO | Single-objective | Constrained Bayesian Optimization with GP surrogate |
| SMAC | Single-objective | Sequential Model-based Algorithm Configuration |
| RoSE-Opt | Single-objective | Bayesian Optimization with PPO agent |
| NSGA-II | Multi-objective | Non-dominated Sorting Genetic Algorithm II |
| MOEA/D | Multi-objective | Multi-objective EA based on Decomposition |
| Random | Baseline | Random search for comparison |

---

## 📁 Repository Structure

```
OpenOpt/
├── sram_compiler/
│   ├── subcircuits/                    # Circuit building blocks
│   │   ├── base_subcircuit.py          # Base class for all subcircuits
│   │   ├── sram_6t_core_for_yield.py   # 6T SRAM cell and array generator
│   │   ├── wordline_driver.py          # Word-line driver (NAND + INV)
│   │   ├── precharge_and_write_driver.py  # Precharge & write driver
│   │   ├── mux_and_sa.py               # Column mux & sense amplifier
│   │   ├── decoder.py                  # Address decoder
│   │   ├── sram_cell_parasitics.py     # Parasitic models for SRAM cells
│   │   └── standard_cell.py            # Standard cells (NAND, INV)
│   ├── testbenches/
│   │   ├── base_testbench.py           # Base testbench with timing setup
│   │   ├── sram_6t_core_testbench.py   # Single-run testbench
│   │   └── sram_6t_core_MC_testbench.py  # Monte Carlo testbench
│   └── config_yaml/                    # Circuit configuration files
│       ├── global.yaml                 # Global simulation parameters
│       ├── sram_6t_cell.yaml           # 6T cell transistor sizing
│       ├── wordline_driver.yaml        # WL driver parameters
│       ├── precharge.yaml              # Precharge circuit parameters
│       ├── write_driver.yaml           # Write driver parameters
│       ├── sa.yaml                     # Sense amplifier parameters
│       ├── mux.yaml                    # Column mux parameters
│       └── decoder.yaml                # Decoder parameters
├── equivalent_modeling/                # Equivalent circuit model
│   ├── main_sram.py                    # Main script for equiv model experiments
│   ├── run.sh                          # Batch run script
│   ├── test.ipynb                      # Result analysis notebook
│   └── results/                        # Experiment results
├── size_optimization/                  # Optimization algorithms
│   ├── exp_utils.py                    # Common utilities and base classes
│   ├── config_sram.yaml                # Optimization configuration
│   ├── demo_nsgaii.py                  # NSGA-II optimizer
│   ├── demo_moead.py                   # MOEA/D optimizer
│   ├── demo_cbo.py                     # Constrained Bayesian Optimization
│   ├── demo_smac.py                    # SMAC optimizer
│   ├── demo_pso.py                     # Particle Swarm Optimization
│   ├── demo_sa.py                      # Simulated Annealing
│   ├── demo_roseopt.py                 # RoSE-Opt integration
│   ├── demo_random.py                  # Random search baseline
│   └── NSGA-II/                        # NSGA-II core implementation
│       ├── problem.py                  # Problem definition
│       ├── individual.py               # Individual representation
│       ├── population.py               # Population management
│       ├── evolution.py                # Evolution main loop
│       └── nsga2_utils.py              # Non-dominated sort, crowding distance
├── tran_models/                        # FreePDK45 transistor models
│   ├── models_TT.spice                 # Typical-Typical corner
│   ├── models_FF.spice                 # Fast-Fast corner
│   ├── models_SS.spice                 # Slow-Slow corner
│   ├── models_FS.spice                 # Fast-Slow corner
│   └── models_SF.spice                 # Slow-Fast corner
├── sim/                                # Simulation output directory
├── environment.yml                     # Conda environment definition
├── experiment.py                       # Joint optimization entry
├── config.py                           # Configuration loader
├── utils.py                            # Utility functions
├── main_sram.py                        # Main simulation entry
├── plot_data.py                        # Visualization utilities
└── OpenOpt_README.md                   # This document
```

---

## ⚙️ Installation

### Clone the Repository

```bash
git clone https://github.com/YourOrg/OpenOpt.git
cd OpenOpt
```

### Python Environment

```bash
conda env create -f environment.yml
conda activate OpenOPT
```

### External Tools

- **ngspice** and **Xyce** are included in `environment.yml`
- **FreePDK45**: Transistor models (included in `tran_models/`)

---

## 🚀 Quick Start

### 1. Run Equivalent Circuit Model Experiment

Compare simulation time and accuracy between full-array and equivalent model:

```bash
cd equivalent_modeling
python main_sram.py
```

This generates results comparing:
- Simulation time (with/without equivalent model)
- Read/write delay accuracy
- Power consumption accuracy

### 2. Run Joint Optimization

```bash
python experiment.py
```

You will be prompted to select:
- Circuit mode: real cell or equivalent cell
- Maximum iterations
- Optimization algorithm (SA/PSO/SMAC/CBO/RoSE-Opt/MOEAD/NSGA-II/Random)

### 3. Configure Global Parameters

Edit `sram_compiler/config_yaml/global.yaml`:

```yaml
vdd: 1.0                    # Supply voltage (V)
temperature: 45             # Temperature (°C)
num_rows: 32                # SRAM array rows
num_cols: 16                # SRAM array columns
monte_carlo_runs: 30        # Number of MC iterations
pdk_path_TT: "tran_models/models_TT.spice"
```

### 4. Run with Equivalent Model Acceleration

```python
from sram_compiler.testbenches.sram_6t_core_MC_testbench import Sram6TCoreMcTestbench

mc_testbench = Sram6TCoreMcTestbench(
    sram_config,
    gen_unused_cells=False,  # Enable equivalent model (False = use equiv model)
    w_rc=True,
    vth_std=0.05,
    coner="TT",
    sim_path="sim"
)

# Run simulation with acceleration
r_delay, r_pavg, r_pstc, r_pdyn = mc_testbench.run_mc_simulation(
    operation="read",
    target_row=31, target_col=15,
    mc_runs=30,
    temperature=45
)
```

### 5. Run Optimization Algorithms

Run the main script which includes the optimization module:

```bash
python experiment.py
```

After the Monte Carlo simulation completes, you'll be prompted to select optimization settings:

Select circuit mode:
  Enter 1 for real circuit
  Enter 2 for equivalent circuit

Enter the maximum number of iterations for joint optimization:
  Enter an integer (default=40)

Select optimization algorithm for joint optimization:
  Enter number (1=SA, 2=PSO, 3=SMAC, 4=CBO, 5=RoSE_Opt, 6=MOEAD, 7=MOBO, 8=NSGA-II)
  Or enter name (SA/PSO/SMAC/CBO/RoSE_Opt/MOEAD/MOBO/NSGA-II)

Output
Results are saved in:
size_optimization/experiment/<algorithm>/  - Optimization results and logs
size_optimization/sim/                     - Simulation outputs

---

## 📊 Equivalent Circuit Model

### Model Design

OpenOpt proposes an equivalent circuit model that simplifies inactive SRAM cells:

**1. BL and BLB Terminal Model**

When WL is pulled low, the access transistor is completely off. The input current at BL/BLB terminals is proportional to voltage change rate, modeled as a capacitor to ground:

```
C_BL = ∫i(t)dt / ΔV
```

**2. WL Terminal Model**

The WL terminal exhibits piecewise behavior:
- Low voltage: Pure capacitive load
- Above threshold: Additional RC network

A simplified single capacitance model `C_WL` is used for overall simulation speedup.

**3. Static Power Model**

After circuit stabilization, the input current at VDD remains constant:

```
R_static = V_DD / I_static
```

**4. Linear Scalability**

For m×n arrays, equivalent parameters scale linearly:

```
C_BL,total = (m - 1) × C_BL,unit
C_WL,total = (n - 1) × C_WL,unit
R_static,total = R_static,unit / (m × n - 1)
```

### Simulation Accuracy

| Metric | 32×16 | 128×64 | 512×512 |
|--------|-------|--------|---------|
| D_rd | −0.05% | -0.03% | −0.01% |
| P_rd,avg | 0.50% | −0.86% | −0.92% |
| P_rd,dyn | 0.53% | −0.92% | −0.97% |
| P_rd,stc | −0.83% | 0.60% | 0.79% |
| D_wr | 0.03% | 0.06% | 0.22% |
| P_wr,avg | −1.27% | −0.67% | −0.59% |
| P_wr,dyn | −1.28% | −0.71% | −0.69% |
| P_wr,stc | −0.79% | 0.32% | 1.68% |

**Key Observations:**
- Read/write delay error consistently <0.22% across all tested configurations
- Power error <1.68% for all metrics, even at 512×512 scale
---

## 📊 Optimization Framework

### Design Space

OpenOpt supports a mixed design space with a capacity constraint:

```
r × c × n_a = Capacity
```

Where Capacity = 32KB × 8 = 262,144 bits (configurable).

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| num_rows | Discrete | {16, 32, ..., 512} | Array row count |
| num_cols | Discrete | {16, 32, ..., 512} | Array column count |
| num_arrays | Derived | Capacity / (rows × cols) | Array count under capacity constraint |
| W_PD | Continuous | 45nm - 135nm | Pull-down NMOS width |
| W_PU | Continuous | 45nm - 135nm | Pull-up PMOS width |
| W_PG | Continuous | 67.5nm - 202.5nm | Pass-gate NMOS width |
| L | Continuous | 30nm - 100nm | Channel length |
| nmos_model_name | Categorical | NMOS_VTL/VTG/VTH | NMOS threshold model |
| pmos_model_name | Categorical | PMOS_VTL/VTG/VTH | PMOS threshold model |

### Figure of Merit (FoM)

```
FoM = log₁₀(SNM_min / (P_max × D_max × √total_area))
```

Where:
- `SNM_min = min(Hold_SNM, Read_SNM, Write_SNM)`
- `P_max = max(P_read, P_write)`
- `D_max = max(T_read, T_write)`

### Algorithm Configurations

Budgets are defined by `experiment.py` (interactive) or in each demo script:

| Algorithm | Key Parameters |
|-----------|----------------|
| SA | T₀=1000, T_min=10⁻⁷, α=0.98 |
| PSO | Population=20, w=0.7, c1=c2=1.4 |
| CBO | GP surrogate, constrained EI |
| SMAC | Random Forest surrogate |
| RoSE-Opt | Bayesian Optimization + PPO |
| MOEA/D | h=17, generations=800, T=20 |
| NSGA-II | Population=1200 |

---

## 📈 Benchmarking Results

### Optimization Algorithm Comparison (32KB SRAM, FreePDK45)

| Measure | w/o Opt. | MOEA/D | NSGA-II | SMAC | RoSE-Opt | SA | CBO | PSO |
|---------|----------|--------|---------|------|----------|-----|-----|-----|
| Array Size | 16×16 | **64×32** | 64×32 | 64×32 | 64×32 | 64×32 | 32×32 | 32×32 |
| Array Num. | 1024 | 128 | 128 | 128 | 128 | 128 | 256 | 256 |
| Column Mux | Off | On | On | On | On | On | On | On |
| NMOS Model | VTG | VTG | VTG | VTH | VTG | VTL | VTL | VTL |
| PMOS Model | VTG | VTH | VTH | VTH | VTH | VTH | VTH | VTL |
| W_PD (µm) | 0.205 | **0.072** | 0.075 | 0.108 | 0.079 | 0.072 | 0.045 | 0.045 |
| W_PU (µm) | 0.090 | **0.072** | 0.080 | 0.072 | 0.082 | 0.108 | 0.048 | 0.049 |
| W_PG (µm) | 0.135 | **0.162** | 0.158 | 0.108 | 0.154 | 0.162 | 0.107 | 0.156 |
| L (nm) | 50.00 | 50.47 | 52.08 | 40.00 | 52.03 | 60.00 | 71.85 | 70.01 |
| T_read (ns) | 2.564 | **2.274** | 2.271 | 2.394 | 2.259 | 2.259 | 2.448 | 2.430 |
| T_write (ns) | 0.750 | **0.638** | 0.637 | 0.626 | 0.636 | 0.628 | 0.721 | 0.679 |
| P_max (mW) | 3.331 | **1.923** | 1.889 | 1.787 | 1.887 | 2.259 | 1.658 | 1.847 |
| min SNM (V) | 0.174 | **0.290** | 0.276 | 0.270 | 0.268 | 0.314 | 0.315 | 0.365 |
| Area (mm²) | 0.4773 | **0.1253** | 0.1262 | 0.1211 | 0.1259 | 0.1338 | 0.2042 | 0.2270 |
| **FoM** | 7.4689 | **8.2721** | 8.2577 | 8.2591 | 8.2482 | 8.2263 | 8.2356 | 8.2316 |

## 🔧 Advanced Usage

### Process Corner Analysis

```python
from config import SRAM_CONFIG
from sram_compiler.testbenches.sram_6t_core_MC_testbench import Sram6TCoreMcTestbench

sram_config = SRAM_CONFIG()
sram_config.load_all_configs(...)

for corner in ["TT", "FF", "SS", "FS", "SF"]:
    mc_testbench = Sram6TCoreMcTestbench(
        sram_config,
        coner=corner,
        gen_unused_cells=False,  # Use equivalent model
        use_mc=True,
        vth_std=0.05,
    )
    result = mc_testbench.run_mc_simulation(
        operation="read_snm",
        target_row=31, target_col=15,
        mc_runs=30
    )
    print(f"{corner}: Read SNM = {result}")
```

### Custom Sizing Evaluation

```python
from size_optimization.exp_utils import evaluate_sram

# Define sizing parameters
params = {
    'pd_width': 0.072e-6,
    'pu_width': 0.072e-6,
    'pg_width': 0.162e-6,
    'length': 50e-9,
    'nmos_model_name': 'NMOS_VTG',
    'pmos_model_name': 'PMOS_VTH'
}

objectives, constraints, result, success = evaluate_sram(params)
if success:
    print(f"FoM: {result['merit']:.4f}")
```

---

## 📚 API Reference

### Core Classes

| Class | Description |
|-------|-------------|
| `SRAM_CONFIG` | Configuration loader from YAML files |
| `Sram6TCoreMcTestbench` | Monte Carlo testbench with equivalent model support |
| `ModifiedSRAMParameterSpace` | Optimization parameter space handler |
| `BaseOptimizer` | Abstract base class for all optimizers |

### Key Functions

| Function | Description |
|----------|-------------|
| `evaluate_sram(params)` | Evaluate SRAM with given parameters |
| `estimate_bitcell_area(...)` | Estimate bit-cell area from W/L |
| `run_mc_simulation(...)` | Run Monte Carlo simulation |

### Equivalent Model Parameters

| Parameter | Description |
|-----------|-------------|
| `gen_unused_cells` | False = use equivalent model, True = full array |
| `pi_res` | π-network resistance (Ω) |
| `pi_cap` | π-network capacitance (pF) |

---

## 🗓️ Changelog

### v1.0.0 (2026)
- Equivalent circuit model 
- Architecture-sizing co-optimization framework
- Multiple optimization algorithms (SA, PSO, CBO, SMAC, RoSE-Opt, NSGA-II, MOEA/D, Random)
- Five process corner support (TT/FF/SS/FS/SF)
- FreePDK45 integration
