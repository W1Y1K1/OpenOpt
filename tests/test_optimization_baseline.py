"""Regression checks for the optimization/compiler baseline contract."""
import contextlib
import io
import unittest

import numpy as np

from size_optimization.exp_utils import (
    CompositeSRAMParameterSpace,
    _load_sram_config_from_yaml,
    apply_params_to_sram_config,
)
from sram_compiler.sizing import resolve_driver_sizes
from sram_compiler.sizing.table import physical_context


class OptimizationBaselineTests(unittest.TestCase):
    def setUp(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.space = CompositeSRAMParameterSpace()
            config = _load_sram_config_from_yaml()
        self.context = physical_context(
            False, interconnect=config.global_config.interconnect,
        )
        self.drivers = resolve_driver_sizes(
            config, mux=False, physical_context=self.context,
        )

    def test_bitcell_candidates_keep_the_frozen_peripheral_baseline(self):
        rng = np.random.default_rng(7)
        dimensions = self.space.bounds.shape[1]
        vectors = [np.zeros(dimensions), np.ones(dimensions)]
        vectors.extend(rng.random((8, dimensions)))
        candidates = []
        for vector in vectors:
            with self.subTest(vector=vector.tolist()):
                with contextlib.redirect_stdout(io.StringIO()):
                    config = _load_sram_config_from_yaml()
                params = self.space.convert_params(vector)
                candidates.append(params)
                apply_params_to_sram_config(config, params)
                self.drivers.validate_for(
                    config, 'SRAM_6T_CELL', False, context=self.context,
                )
        self.assertNotEqual(candidates[0]['pd_width'], candidates[1]['pd_width'])
        self.assertNotEqual(candidates[0]['length'], candidates[1]['length'])

    def test_changed_periphery_still_requires_a_new_baseline(self):
        with contextlib.redirect_stdout(io.StringIO()):
            config = _load_sram_config_from_yaml()
        config.wordline_driver.nmos_width.value[0] *= 1.1
        with self.assertRaisesRegex(ValueError, 'baseline peripheral configuration'):
            self.drivers.validate_for(
                config, 'SRAM_6T_CELL', False, context=self.context,
            )


if __name__ == '__main__':
    unittest.main()
