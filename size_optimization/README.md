# SRAM optimization

OpenOpt includes circuit-backed optimization and a separate offline surrogate
package. Run commands from the repository root.

## Circuit-backed algorithms

```bash
python -m pip install -r requirements-optimization.txt
python main_sram.py circuit-optimize --help
python main_sram.py circuit-optimize --algorithm sa --max-iter 5 --seed 1
```

| Algorithms | CLI names |
|---|---|
| Simulated annealing, particle swarm, random | `sa`, `pso`, `random` |
| CMA-ES, SMAC | `cmaes`, `smac` |
| Bayesian and surrogate methods | `cbo`, `roseopt`, `cpn`, `tssbo` |
| Multi-objective methods | `mobo`, `moead`, `nsgaii` |

`config_sram.yaml` defines bitcell search parameters; `exp_utils.py` connects
algorithms to the current compiler and Xyce. Peripheral YAML values, driver
sizing and timing stay fixed across cell candidates. Peripheral resizing
requires a separately characterized baseline and is outside this search space.
Check solver success and inspect the final candidate using a full-array
reference before interpreting approximate-mode metrics.

For joint architecture/sizing search or sizing at fixed configurations:

```bash
python main_sram.py circuit-experiment
```

The interactive command selects circuit mode, algorithm, seed and iteration
budget. The root `experiment.py` forwards to the same entrance.
Generated optimization outputs are ignored by Git.

## Offline surrogate algorithms

`openyield_v2/` contains evolutionary, Bayesian and TabPFN-based searches.
It reads bundled static training data and does not call Xyce during optimization.

```bash
python -m pip install -r size_optimization/openyield_v2/requirements.txt
python main_sram.py experiment --dry-run
python main_sram.py optimize --family evolutionary -- --help
python main_sram.py compare -- --help
```

The [offline guide](openyield_v2/README.md) explains its configuration, data
conditions and outputs. TabPFN may require model access and a model download on
first use. Algorithm modules load only when their workflow is selected.

See [source revision](../UPSTREAM.md) and [compiler configuration](../sram_compiler/README.md).

The optimizer/compiler boundary has a focused regression check:

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
