# Driver sizing and timing

The compiler resolves driver widths and timing before evaluating cell candidates.
Keep these choices fixed across equivalent-mode and candidate comparisons.

`global.yaml` selects `sizing.mode: lookup` and `timing.mode: lookup`.
`sizing_lookup.json` defines array-class peripheral multipliers;
`timing_lookup.json` defines the matching schematic clock policy. Dimensions
round up to the next class within the 512-row by 256-column timing envelope.

The additional `layout_*_lookup.json` files are frozen upstream profiles consumed
by the optional `--compact-control` simulation setting. OpenOpt includes their
simulation inputs but no layout generators. Profiles retain their source
metadata and scope; selecting a profile does not validate a new configuration.

```bash
python main_sram.py simulate --rows 8 --cols 4 --no-run-xyce
python main_sram.py simulate --help
```

Use `--sizing-lookup` and `--timing-lookup` for explicit alternative tables, or
`--period` for a fixed diagnostic clock in seconds. Changed periphery, model,
interconnect or control architecture must not silently reuse a stale baseline.
See the [compiler guide](../README.md) and [upstream scope](../../UPSTREAM.md).
