"""Reproduce the bounded eleven-rune window census."""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / 'scripts/wing_tree_windows.py'), run_name='__main__')
