"""Compatibility entrance for interactive architecture and sizing search."""
import sys

from main_sram import main

if __name__ == '__main__':
    raise SystemExit(main(['circuit-experiment', *sys.argv[1:]]))
