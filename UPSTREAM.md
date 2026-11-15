# Source and migration scope

The current compiler and optimization code is adapted from
[ShenShan123/OpenYield](https://github.com/ShenShan123/OpenYield), commit
`ccd45b4a127402378c1e61d8596da066993ca52c` (compiler V2.2.9).

Included components are `sram_compiler` configuration, circuit blocks,
testbenches, equivalent models, timing/sizing policies, interconnect support,
`utils`, `tran_models`, and `size_optimization` with its runtime resources.
The shared variation code remains an internal compiler dependency. OpenOpt's
main entrance defaults to nominal simulation; no yield-estimation package or
yield workflow is distributed.

Layout generators and extraction commands are excluded. The pure SPICE
parsing, flattening and profile-rendering helpers required by calibrated RC
simulation were moved from upstream `layout/freepdk45/` to `rc_support/`.
The supplied reference RC profiles and sizing/timing JSON files retain their
upstream scope and metadata. They are runtime inputs, not new validation results.

OpenOpt adaptations include the scoped command dispatcher, nominal script
default, compatibility entrances, dependency lists and usage documentation.
The composite circuit-backed search fixes peripheral parameters at their YAML
values to respect the compiler's frozen driver/timing baseline. Upstream's
variable-peripheral candidates conflict with that evaluator contract. The
solver-side baseline checks remain intact. Other numerical implementations follow
the upstream revision. The upstream code is distributed under the included
[Apache 2.0 license](LICENSE).

The original OpenOpt implementation is preserved in Git at
`e69ba2e2f63bad11fa7853662871545b0d18e055`. Its committed
`equivalent_modeling/results/` artifacts are retained unchanged. They describe
the original implementation and are not results from the updated compiler.
