"""Recompute the archived quadratic certificate without overwriting it."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts'))
from run_quadratic_palette import produce

if __name__ == '__main__':
    result = produce()
    assert result == json.loads((ROOT/'exports/literal-prime-quadratic.json').read_bytes())
    print('Full quadratic certificate reproduced: 21,924 anchor triples.')
