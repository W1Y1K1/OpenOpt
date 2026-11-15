# SRAM circuit compiler

The compiler assembles 6T or 10T arrays, decoders, precharge/write drivers,
sense amplifiers, column multiplexers and timing control. Full-transistor and
equivalent-circuit modes share the same configuration and measurement path.
The core is imported from OpenYield V2.2.9; see [source scope](../UPSTREAM.md).

## Commands

Run from the repository root:

```bash
python main_sram.py simulate --help
python main_sram.py simulate --rows 2 --cols 2 --operation read --no-run-xyce
python main_sram.py simulate --rows 8 --cols 4 --operation write --run-xyce
python main_sram.py simulate --cell-type SRAM_10T_CELL --rows 2 --cols 2 --no-run-xyce
```

`main_sram.py` defaults to nominal simulation. Optional shared compiler
variation modes are available for circuit diagnostics; this distribution does
not include yield-estimation workflows.

## Configuration

`config_yaml/loader.py` loads circuit YAMLs through `SRAM_CONFIG` without
rewriting the source configuration. `global.yaml` sets array dimensions,
supply, temperature, equivalent mode, timing, and wiring. Device dimensions
are in metres. The default target is the last row and column.

The supported timing lookup covers 512 rows by 256 columns. A manual `--period`
is a diagnostic override. Standard 6T arrays use a 2:1 mux when enabled; writes
drive the selected row's columns. SNM commands construct a single-cell testbench.

The distributed interconnect configuration includes a scoped reference RC
profile; metadata records whether that profile applies. Outside its scope,
the configuration retains illustrative wiring. Keep the selected profile,
timing and sizing fixed when comparing equivalent modes.

## Python API

```python
from sram_compiler.config_yaml.loader import load_config
from sram_compiler.testbenches.sram_6t_core_MC_testbench import Sram6TCoreMcTestbench

config = load_config(8, 4, "TT")
tb = Sram6TCoreMcTestbench(
    config, corner="TT", variation_mode="nominal", real_cell_mode=0,
    sim_path="outputs/api_example",
)
circuit = tb.create_testbench("read", 7, 3)
```

See [commands](experiments/README.md), [equivalent modes](equivalent_modeling/README.md),
[sizing and timing](sizing/README.md), and [optimization](../size_optimization/README.md).
