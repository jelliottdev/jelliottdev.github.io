"""Portable replay of the frozen target and both complete-search references."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).with_name('execute_matching.py')), run_name='__main__')
