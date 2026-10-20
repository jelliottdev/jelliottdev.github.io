"""Reproduce the direct polynomial stream bound."""
import runpy
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / 'scripts/polynomial_stream_bound.py'), run_name='__main__')
