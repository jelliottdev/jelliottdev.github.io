"""Reproduce the fixed directional prime-path baseline; no probability test."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from grid_prime_paths import report

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
result = report()
if args.check:
    expected = json.loads(Path(__file__).with_name('results.json').read_text(encoding='utf-8'))
    assert result == expected
    print('PASS: all paths, counts, prime values and coordinates match the baseline')
else:
    print(json.dumps(result, indent=2))
