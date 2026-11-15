"""Compatibility entrance for the current equivalent-circuit comparison."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    os.chdir(ROOT)
    from sram_compiler.experiments.equivalent import main

    raise SystemExit(main())
