"""Reproduce all 16 LP2-15 entries. Python 3, standard library only.

Run without arguments to print the ledger; --write saves it; --check compares
it with the saved ledger. Does not search keys or alter manuscript numbers.
"""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/fibonacci-prime-panel.json'


def report():
    path = ROOT / 'data/pages/lp2-15.json'
    page = json.loads(path.read_bytes())
    # Standard Fibonacci sequence, retaining only one occurrence of 1.
    fib, a, b = [], 0, 1
    while len(fib) < 16:
        if not fib or a != fib[-1]:
            fib.append(a)
        a, b = b, a + b
    primes, candidate = [], 2
    while len(primes) <= fib[-1]:
        if all(candidate % d for d in range(2, isqrt(candidate) + 1)):
            primes.append(candidate)
        candidate += 1
    # Start at the red cell, then right, down, left twice, up twice, ...
    r, c, coords = 1, 1, [(1, 1)]
    length = 1
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    direction = 0
    while len(coords) < 16:
        for _ in range(2):
            dr, dc = directions[direction % 4]
            for _ in range(length):
                if len(coords) == 16:
                    break
                r, c = r + dr, c + dc
                coords.append((r, c))
            direction += 1
        length += 1
    assert len(set(coords)) == 16 and all(0 <= r < 4 and 0 <= c < 4 for r, c in coords)
    rows = []
    for step, (f, (r, c)) in enumerate(zip(fib, coords), 1):
        p = primes[f]
        signed = 3301 - p
        printed = page['numbers'][r][c]
        assert abs(signed) == printed, (step, f, r, c)
        rows.append(dict(step=step, row=r + 1, column=c + 1,
                         fibonacci_index=f, one_based_prime_rank=f + 1,
                         prime=p, signed_distance=signed,
                         absolute_distance=abs(signed), printed=printed))
    return dict(page='lp2-15', source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                original_image_sha256=page['image_sha256'],
                formula='printed = abs(3301 - prime[F]); prime[0] = 2',
                convention='Fibonacci values 0,1,2,3,...987; duplicate initial 1 omitted; image coordinates one-based.',
                rows=rows, matching_entries=len(rows),
                scope='Reproduction of a previously documented construction, not a new discovery or a decryption rule.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert json.loads(OUTPUT.read_bytes()) == result, 'Saved ledger differs'
        print('PASS: all 16 printed entries and the saved ledger match.')
    elif args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
    else:
        print(json.dumps(result, indent=2))
