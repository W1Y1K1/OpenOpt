# Equivalent-circuit models

Mode 0 keeps the full transistor array. Modes 1–4 replace omitted cells with
extracted loads while retaining distributed interconnect segments.

| Mode | Real cells retained |
|---:|---|
| 0 | Entire array |
| 1 | Target row and column |
| 2 | Target row |
| 3 | Target column |
| 4 | Target cell |

`equivalent.mode` in `config_yaml/global.yaml` supplies the default; use
`--real-cell-mode` to override it. Xyce extracts capacitance and leakage for
modes 1–4, even when the final array simulation is disabled. Extraction cache
keys include the cell, model content and physical conditions.

## Compare modes

```bash
python main_sram.py equivalent --help
python main_sram.py equivalent --sizes 16x16,32x16 --modes 0,1,4 --operations read,write --temperature 25 --vdd 1.0
```

Run from the repository root. The comparison defaults to nominal conditions
and uses mode 0 as the reference. Array, target, PVT, wiring, timing and sizing
remain fixed between modes. Use `--mux` to enable the 2:1 column multiplexer.

The runner saves the configuration and metric tables under `outputs/`.
`time_usage_s` uses a monotonic wall clock around testbench construction and
the requested simulations, including extraction and result handling. Configuration
loading happens before that timer. It is not the same timing boundary as the
original OpenOpt script. Extraction caches can affect repeated timings; record
cache state and system load when conducting a runtime study. The comparison
command itself does not perform repeated timing trials.

Use `--plot` to create a metric comparison plot. Inspect reference and equivalent
waveforms for the intended operating conditions before relying on an approximation.

The legacy `python equivalent_modeling/main_sram.py` entrance forwards to this
runner. Historical artifacts in the root `equivalent_modeling/results/` directory
belong to the earlier implementation at commit `e69ba2e`.
