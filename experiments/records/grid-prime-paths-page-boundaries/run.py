"""Audit four-cell straight paths, rejecting paths across manuscript pages. No chance claim.

Keep original page-row order. Reject paths containing 4; do not remove cells.
Leading zeroes remain in the digit string; primality is tested in decimal.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'exports/alphanumeric-grids.json'
OUTPUT = Path(__file__).with_name('results.json')


def prime(n):
    return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))


def report():
    raw = SOURCE.read_bytes()
    records = json.loads(raw)['records']
    assert len(records) == 256
    grid = [records[i:i+8] for i in range(0, 256, 8)]
    for row in grid:
        assert len({(r['page'], r['row']) for r in row}) == 1
        assert [r['column'] for r in row] == list(range(1, 9))
    hits, total, eligible = [], 0, 0
    for y in range(32):
        for x in range(8):
            for dx, dy in itertools.product((-1, 0, 1), repeat=2):
                if (dx, dy) == (0, 0) or not (0 <= x+3*dx < 8 and 0 <= y+3*dy < 32):
                    continue
                cells = [grid[y+i*dy][x+i*dx] for i in range(4)]
                if len({c['page'] for c in cells}) != 1:
                    continue
                total += 1
                digits = ''.join(c['token'][0] for c in cells)
                assert set(digits) <= set('01234')
                if '4' in digits:
                    continue
                eligible += 1
                value = int(digits, 10)
                if prime(value):
                    hits.append({'digits': digits, 'decimal': value,
                                 'base4_value': int(digits, 4),
                                 'base4_value_is_prime': prime(int(digits, 4)),
                                 'suffixes': ''.join(c['token'][1] for c in cells),
                                 'start_xy_zero_based': [x, y], 'step_xy': [dx, dy],
                                 'crosses_page': len({c['page'] for c in cells}) > 1,
                                 'cells': cells})
    universe = sorted({int(''.join(d), 10) for d in itertools.product('0123', repeat=4)
                       if prime(int(''.join(d), 10))})
    counts = Counter(h['decimal'] for h in hits)
    return {'scope': __doc__, 'source': str(SOURCE.relative_to(ROOT)).replace('\\', '/'),
            'source_sha256': hashlib.sha256(raw).hexdigest(),
            'coordinates': 'Zero-based x is column; y increases downward through 32 concatenated rows. No wrapping; page crossings forbidden.',
            'total_directed_paths': total, 'eligible_paths': eligible,
            'rejected_paths_containing_4': total-eligible,
            'prime_occurrences': len(hits), 'distinct_primes': len(counts),
            'prime_universe_size': len(universe),
            'missing_primes': [n for n in universe if not counts[n]],
            'frequencies': [{'decimal': n, 'digits': f'{n:04d}', 'count': counts[n]} for n in universe],
            'hits': hits}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument('--write', action='store_true')
    options.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: path counts, all prime occurrences and source coordinates reproduced')
    elif args.write:
        OUTPUT.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8', newline='\n')
        print('Wrote local results.json')
    else:
        print(json.dumps(result, indent=2))
