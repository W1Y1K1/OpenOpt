# OpenOpt

OpenOpt is an open-source SRAM architecture and transistor-sizing optimization
tool. It builds 6T and 10T SRAM circuits, evaluates them with Xyce, and provides
equivalent-circuit models for exploring array configurations and device sizes.

The circuit and optimization implementation is synchronized from
[OpenYield V2.2.9](https://github.com/ShenShan123/OpenYield/tree/ccd45b4a127402378c1e61d8596da066993ca52c).
This distribution focuses on circuit evaluation, equivalent models and
optimization. Yield-estimation algorithms and layout-generation workflows are
not included. See [UPSTREAM.md](UPSTREAM.md) for the source revision and scope.

## Install

Use Linux, or a compatible Linux environment such as WSL2. Run commands from
the repository root:

```bash
git clone https://github.com/W1Y1K1/OpenOpt.git
cd OpenOpt
conda env create -f environment.yml
conda activate openopt
command -v Xyce
Xyce -v
python main_sram.py --help
```

The environment provides the circuit dependencies and Xyce. To use an existing
Python environment, install `requirements.txt` and provide Xyce on `PATH`.
Circuit-backed optimization has additional dependencies:

```bash
python -m pip install -r requirements-optimization.txt
```

## Generate and simulate a circuit

Generate a small full-transistor deck:

```bash
python main_sram.py simulate --rows 2 --cols 2 --operation read --variation-mode nominal --real-cell-mode 0 --no-run-xyce
```

Run a read or write simulation:

```bash
python main_sram.py simulate --rows 8 --cols 4 --operation read --variation-mode nominal --real-cell-mode 0 --run-xyce
python main_sram.py simulate --rows 8 --cols 4 --operation write --variation-mode nominal --real-cell-mode 1 --run-xyce
```

The settings in `main_sram.py` provide defaults; command-line arguments override
them. OpenOpt defaults to nominal simulation. Use `--corner`, `--temperature`,
`--vdd`, `--target-row` and `--target-col` to select conditions. Configuration,
decks, logs and results are saved under ignored `outputs/` directories.

## Equivalent-circuit models

| Mode | Transistor-level cells retained |
|---:|---|
| 0 | Full array, used as the reference |
| 1 | Target row and target column |
| 2 | Target row |
| 3 | Target column |
| 4 | Target cell |

Modes 1–4 extract equivalent capacitances and leakage from the selected cell
and model conditions. Xyce is needed during parameter extraction, including
when the final array deck is generated with `--no-run-xyce`.

Compare modes under the same array and operating conditions:

```bash
python main_sram.py equivalent --sizes 16x16,32x16 --modes 0,1,4 --operations read,write --corner TT --temperature 25 --vdd 1.0
```

See the [equivalent-model guide](sram_compiler/equivalent_modeling/README.md)
for output files and timing definitions. Compare approximate modes with mode 0
for the intended configuration; inspect waveforms when assessing circuit behavior.

## Optimization

Circuit-backed algorithms include SA, PSO, random search, CMA-ES, SMAC, CBO,
RoSE-Opt, CPN, TSSBO, MOBO, MOEA/D and NSGA-II.

```bash
python main_sram.py circuit-optimize --algorithm sa --max-iter 5 --seed 1
python main_sram.py circuit-optimize --algorithm pso --max-iter 5 --seed 1
python main_sram.py circuit-experiment
```

`size_optimization/config_sram.yaml` defines optimization settings. The
interactive `circuit-experiment` command supports joint architecture/sizing
search and sizing at fixed configurations.

A separate offline surrogate package operates on bundled training datasets:

```bash
python -m pip install -r size_optimization/openyield_v2/requirements.txt
python main_sram.py experiment --dry-run
python main_sram.py optimize --family evolutionary -- --help
```

The offline package does not call Xyce during optimization. Its training data
retain their original collection conditions. See the
[optimization guide](size_optimization/README.md) for algorithm calls and dependencies.

## Configuration and API

Circuit YAML files live in `sram_compiler/config_yaml/`; transistor widths and
lengths use metres. The timing lookup covers up to 512 rows and 256 columns.
Use the same timing, driver sizes, PVT and interconnect settings when comparing
equivalent modes or cell candidates.

```python
from sram_compiler.config_yaml.loader import load_config
from sram_compiler.testbenches.sram_6t_core_MC_testbench import Sram6TCoreMcTestbench

config = load_config(8, 4, "TT")
testbench = Sram6TCoreMcTestbench(
    config,
    corner="TT",
    variation_mode="nominal",
    real_cell_mode=0,
    sim_path="outputs/python_example",
)
circuit = testbench.create_testbench("read", 7, 3)
```

Further usage: [compiler](sram_compiler/README.md),
[commands](sram_compiler/experiments/README.md),
[sizing and timing](sram_compiler/sizing/README.md).
