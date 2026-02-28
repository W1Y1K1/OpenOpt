# **OpenOpt: An Open-Source SRAM Optimizer Based on Equivalent Circuit Model**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-Apache--2.0-green.svg)
![PDK](https://img.shields.io/badge/PDK-FreePDK45-orange.svg)
![Speedup](https://img.shields.io/badge/Speedup-up%20to%2061.4×-brightgreen.svg)

This repository contains the implementation of:

**OpenOpt: An Open-Source SRAM Architecture and Sizing Co-Optimization Framework Based on Equivalent Circuit Model**

OpenOpt addresses the PPA (Power, Performance, Area) trade-off challenges and large-scale array SPICE simulation efficiency bottlenecks in SRAM design. It provides a comprehensive co-optimization platform that jointly searches architecture parameters (row/column counts, multiplexing ratio) and transistor-level sizing within a unified design space.

---

## 📌 Overview

As semiconductor process nodes continue to scale down, SRAM design faces two major bottlenecks:

1. **Simulation Efficiency**: Full-array SPICE simulation runtime grows exponentially with array size, making iterative optimization prohibitive for large-scale SRAM arrays.

2. **Joint Optimization**: SRAM performance depends on both architecture configuration and transistor sizing. Traditional methods separate these aspects, making it difficult to find globally optimal solutions.

OpenOpt addresses these challenges through:

- **Equivalent Circuit Model**: Simplifies inactive SRAM cells into equivalent RC loads and static power models, achieving up to **61.4× simulation speedup** while maintaining high fidelity (read/write delay error <0.05%, power error <1.28%)

- **Architecture-Sizing Co-optimization**: Joint search space covering row/column counts, multiplexing ratio, transistor W/L, and threshold types

- **Seven Optimization Algorithms**: SA, PSO, CBO, SMAC, RoSE-Opt, NSGA-II, and MOEA/D

---

## ✨ Highlights

### ✔️ Equivalent Circuit Model for Simulation Acceleration

- **BL/BLB Terminal Model**: Capacitor-to-ground equivalent for inactive cells
- **WL Terminal Model**: Simplified capacitance model capturing piecewise behavior
- **Static Power Model**: Large resistance from VDD to ground
- **Linear Scalability**: Computational complexity decoupled from array size
- **High Fidelity**: <0.05% delay error, <1.28% power error for medium-scale arrays

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
| Architecture | mux_ratio | Column multiplexing ratio |
| Architecture | num_arrays | Number of arrays under capacity constraint |
| Transistor | W_PD, W_PU, W_PG | Transistor widths |
| Transistor | L | Channel length |
| Transistor | Vth_type | Threshold voltage type (VTL/VTG/VTH) |

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
│   ├── demo_mobo.py                    # Multi-objective Bayesian Optimization
│   ├── demo_cbo.py                     # Constrained Bayesian Optimization
│   ├── demo_smac.py                    # SMAC optimizer
│   ├── demo_pso.py                     # Particle Swarm Optimization
│   ├── demo_sa.py                      # Simulated Annealing
│   ├── demo_roseopt.py                 # RoSE-Opt integration
│   ├── demo_random.py                  # Random search baseline
│   ├── sram_lef_generator.py           # LEF file generator for P&R
│   └── NSGA-II/                        # NSGA-II core implementation
│       ├── problem.py                  # Problem definition
│       ├── individual.py               # Individual representation
│       ├── population.py               # Population management
│       ├── evolution.py                # Evolution main loop
│       └── nsga2_utils.py              # Non-dominated sort, crowding distance
├── MOBO/                               # Multi-objective Bayesian Optimization
│   ├── acquisition.py                  # EHVI acquisition function
│   ├── bayesian_optimizer.py           # Bayesian optimizer core
│   ├── problem.py                      # Problem definition
│   └── main.py                         # MOBO entry point
├── tran_models/                        # FreePDK45 transistor models
│   ├── models_TT.spice                 # Typical-Typical corner
│   ├── models_FF.spice                 # Fast-Fast corner
│   ├── models_SS.spice                 # Slow-Slow corner
│   ├── models_FS.spice                 # Fast-Slow corner
│   └── models_SF.spice                 # Slow-Fast corner
├── sim/                                # Simulation output directory
├── config.py                           # Configuration loader
├── utils.py                            # Utility functions
├── main_sram.py                        # Main simulation entry
├── plot_data.py                        # Visualization utilities
└── README.md
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
conda create -n openopt python=3.10
conda activate openopt

# Install PyTorch
pip install torch==2.0.0 --index-url https://download.pytorch.org/whl/cpu

# Install dependencies
pip install -r requirements.txt
```

### Required Dependencies

```bash
pip install numpy scipy matplotlib pandas pyyaml tqdm
pip install PySpice scikit-learn
pip install smac ConfigSpace    # For SMAC optimizer
pip install botorch gpytorch    # For MOBO optimizer
```

### External Tools

- **ngspice** or **Xyce**: SPICE simulator backend
- **FreePDK45**: Transistor models (included in `tran_models/`)

```bash
# Ubuntu/Debian
sudo apt-get install ngspice

# macOS
brew install ngspice

# Verify
ngspice --version
```

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

### 2. Configure Global Parameters

Edit `sram_compiler/config_yaml/global.yaml`:

```yaml
vdd: 1.0                    # Supply voltage (V)
temperature: 45             # Temperature (°C)
num_rows: 32                # SRAM array rows
num_cols: 16                # SRAM array columns
monte_carlo_runs: 30        # Number of MC iterations
pdk_path_TT: "tran_models/models_TT.spice"
```

### 3. Run with Equivalent Model Acceleration

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

### 4. Run Optimization Algorithms

```bash
# Multi-objective: MOEA/D (best performance)
python size_optimization/demo_moead.py

# Multi-objective: NSGA-II
python size_optimization/demo_nsgaii.py

# Single-objective: SMAC
python size_optimization/demo_smac.py

# Single-objective: SA
python size_optimization/demo_sa.py

# Single-objective: PSO
python size_optimization/demo_pso.py
```

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

### Simulation Speedup Results

| Array Size | Full Simulation | Equivalent Model | Speedup |
|------------|-----------------|------------------|---------|
| 16×16 | 0.54 hr | 0.07 hr | 8.1× |
| 32×32 | 1.75 hr | 0.10 hr | 17.5× |
| 64×64 | 3.50 hr | 0.14 hr | 24.9× |
| 128×128 | 6.20 hr | 0.17 hr | 35.9× |
| 512×512 | 9.80 hr | 0.16 hr | **61.4×** |

### Simulation Accuracy

| Metric | 16×8 | 32×16 | 64×32 |
|--------|------|-------|-------|
| r_delay | -0.25% | -0.05% | 0.04% |
| w_delay | 0.32% | 0.03% | -0.05% |
| r_pavg | 0.21% | 0.50% | 0.76% |
| w_pavg | -8.05% | -1.27% | 0.56% |
| r_pdyn | 0.17% | 0.53% | 0.80% |
| w_pdyn | -8.07% | -1.28% | 0.43% |

**Key Observations:**
- Read/write delay error consistently <0.32%
- Power error <1.28% for medium-scale arrays (32×16)
- Error decreases as array size increases

---

## 📊 Optimization Framework

### Design Space

OpenOpt supports an 8-dimensional mixed design space with capacity constraint:

```
r × c × n_a = Capacity
```

Where Capacity = 32KB × 8 = 262,144 bits (configurable).

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| num_rows | Discrete | {8, 16, ..., 512} | Array row count |
| num_cols | Discrete | {8, 16, ..., 256} | Array column count |
| mux_ratio | Discrete | {1, 2, 4, 8} | Column multiplexing ratio |
| W_PD | Continuous | 45nm - 135nm | Pull-down NMOS width |
| W_PU | Continuous | 45nm - 135nm | Pull-up PMOS width |
| W_PG | Continuous | 67.5nm - 202.5nm | Pass-gate NMOS width |
| L | Continuous | 30nm - 100nm | Channel length |
| Vth_type | Categorical | VTL/VTG/VTH | Threshold voltage type |

### Figure of Merit (FoM)

```
FoM = log₁₀(SNM_min / (P_max × D_max × √Area))
```

Where:
- `SNM_min = min(Hold_SNM, Read_SNM, Write_SNM)`
- `P_max = max(P_read, P_write)`
- `D_max = max(T_read, T_write)`

### Penalty Terms for Architecture Search

**Chip-select delay:**
```
D'_rd = D_rd + τ_cs × log₂(n_a)
D'_wr = D_wr + τ_cs × log₂(n_a)
```

**Mux correction:**
```
D'_rd = D_rd + τ_mux × log₂(n_a)
P'_rd = P_rd + (n_a - 1) × log₂(n_a) × P_mux
```

### Algorithm Configurations

All algorithms use a budget of **1,500 SPICE simulations**:

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

### Key Improvements (MOEA/D vs Baseline)

| Metric | Improvement |
|--------|-------------|
| SNM | **+66.7%** (0.174V → 0.290V) |
| Area | **-73.6%** |
| Read Delay | -11.3% |
| Write Delay | -14.9% |
| Peak Power | **-42.3%** |
| Overall FoM | **+10.8%** |

### Algorithm Characteristics

- **MOEA/D**: Best overall FoM, surpasses threshold of 8.25 after ~150 iterations
- **NSGA-II**: Fast initial convergence, effective elitist strategy
- **RoSE-Opt**: Good balance in low-power region
- **SMAC**: Competitive FoM with Random Forest surrogate
- **SA/PSO**: Lag behind in Area-SNM trade-off

---

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

### Custom Architecture Search

```python
from size_optimization.exp_utils import evaluate_sram

# Define architecture + sizing parameters
params = {
    'num_rows': 64,
    'num_cols': 32,
    'mux_ratio': 2,
    'pd_width': 0.072e-6,
    'pu_width': 0.072e-6,
    'pg_width': 0.162e-6,
    'length': 50e-9,
    'nmos_model': 'NMOS_VTG',
    'pmos_model': 'PMOS_VTH'
}

objectives, constraints, result, success = evaluate_sram(params)
if success:
    print(f"FoM: {result['merit']:.4f}")
```

### LEF File Generation

```python
from sram_lef_generator import generate_sram_lef

filename, macro_name = generate_sram_lef(
    word_size=12,
    num_words=1024,
    pin_width=0.14,
    pin_pitch=2.86,
    output_dir="./lef"
)
```

---

## 🔗 Integration with OpenACMv2

OpenOpt serves as the SRAM optimization engine in the OpenACMv2 ACCO framework:

```
OpenACMv2 ACCO Framework
├── Level-I (Architecture-Level)
│   ├── Multiplier configuration (GNN-based)
│   └── SRAM macro configuration (OpenOpt architecture search)
└── Level-II (Transistor-Level)
    ├── Compressor sizing
    └── SRAM bit-cell sizing (OpenOpt transistor optimization)
```

### Integration Command

```bash
python DCIM_OPT/run_optimization.py \
    --stage width \
    --component sram \
    --algo MOEAD \
    --use_equiv_model True
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
| `BayesianOptimizer` | MOBO with EHVI acquisition |

### Key Functions

| Function | Description |
|----------|-------------|
| `evaluate_sram(params)` | Evaluate SRAM with given parameters |
| `estimate_bitcell_area(...)` | Estimate bit-cell area from W/L |
| `run_mc_simulation(...)` | Run Monte Carlo simulation |
| `generate_sram_lef(...)` | Generate LEF file for P&R |
| `compute_hypervolume(...)` | Compute hypervolume for multi-objective |

### Equivalent Model Parameters

| Parameter | Description |
|-----------|-------------|
| `gen_unused_cells` | False = use equivalent model, True = full array |
| `pi_res` | π-network resistance (Ω) |
| `pi_cap` | π-network capacitance (pF) |

---

## 📜 License

This project is licensed under Apache-2.0. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

OpenOpt builds on:

- **OpenACM** - Approximate CiM compiler framework
- **OpenYield** - Variation-aware SRAM simulation and high-fidelity models
- **PySpice** - Python interface to SPICE simulators
- **FreePDK45** - Open-source 45nm PDK
- **SMAC3** - Sequential Model-based Algorithm Configuration
- **BoTorch** - Bayesian Optimization in PyTorch

---

## 📖 Citation

If you use OpenOpt in your research, please cite:

```bibtex
@inproceedings{openopt2025,
  title     = {OpenOpt: An Open-Source SRAM Optimizer Based on Equivalent Circuit Model},
  author    = {Your Team},
  booktitle = {Proceedings of the Conference},
  year      = {2025},
  note      = {SNM +66.7\%, Area -73.6\%, up to 61.4× simulation speedup}
}
```

---

## 📞 Contact

For questions or issues, please open a GitHub issue or contact the maintainers.

---

## 🗓️ Changelog

### v1.0.0 (2025)
- Initial release
- Equivalent circuit model with up to 61.4× speedup
- Architecture-sizing co-optimization framework
- Seven optimization algorithms (SA, PSO, CBO, SMAC, RoSE-Opt, NSGA-II, MOEA/D)
- Five process corner support (TT/FF/SS/FS/SF)
- FreePDK45 integration
