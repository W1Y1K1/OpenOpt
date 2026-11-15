# OpenOpt commands

Run all commands from the repository root. Script defaults in `main_sram.py`
are overridden by explicit command-line arguments. The main entrance defaults
to nominal simulation.

| Command | Purpose |
|---|---|
| `simulate` | Generate or run read/write and single-cell SNM decks |
| `equivalent` | Compare equivalent modes with the full array |
| `circuit-optimize` | Run one circuit-backed sizing algorithm |
| `circuit-experiment` | Interactive joint architecture/sizing or fixed-configuration search |
| `optimize --family FAMILY` | Run an offline optimization family |
| `compare -- ARGS` | Compare offline algorithms |
| `experiment` | Run the offline campaign configuration |

```bash
python main_sram.py --help
python main_sram.py simulate --help
python main_sram.py simulate --rows 2 --cols 2 --operation read --no-run-xyce
python main_sram.py simulate --rows 8 --cols 4 --operation write --real-cell-mode 1 --run-xyce
python main_sram.py equivalent --sizes 16x16 --modes 0,1,4 --operations read,write
python main_sram.py circuit-optimize --algorithm sa --max-iter 5 --seed 1
python main_sram.py circuit-experiment
python main_sram.py optimize --family evolutionary -- --help
python main_sram.py compare -- --help
python main_sram.py experiment --dry-run
```

Simulation options include `--corner`, `--vdd`, `--temperature`, `--cell-type`,
`--target-row`, `--target-col`, `--interconnect-config`, `--column-mux`,
`--output-dir`, and `--run-xyce` / `--no-run-xyce`. Use `--period` only for an
explicit diagnostic clock override. Equivalent modes need Xyce for extraction.

Generated decks, configuration summaries, solver logs and results go under
ignored output directories. A generated deck verifies construction only.
Circuit behavior should be checked using measures and waveforms.

See [compiler configuration](../README.md), [equivalent models](../equivalent_modeling/README.md)
and [optimization](../../size_optimization/README.md).
