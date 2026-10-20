"""Reproduce exact and anagram word-repeat counts."""
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT/'scripts/word_reset_bound.py'),run_name='__main__')
