"""Test a necessary finite-difference condition for direct polynomial streams.

This is not a test of polynomial keystreams combined with unknown plaintext.
All arithmetic is exact; no coefficient or modulus search is performed.
"""
import argparse
import hashlib
import json
from functools import reduce
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/polynomial-stream-bound.json'


def differences(values):
    return [b - a for a, b in zip(values, values[1:])]


def report():
    paths = ['data/index.json'] + [f'text/lp2-{i:02}.txt' for i in range(56)]
    blobs = {p: (ROOT / p).read_bytes() for p in paths}
    alphabet = json.loads(blobs[paths[0]])['alphabet']
    lookup = {a['rune']: (i, a['prime']) for i, a in enumerate(alphabet)}
    rows, skipped = [], []
    for path in paths[1:]:
        raw = blobs[path].decode('utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - lookup.keys()
        if unknown:
            raise ValueError(f'Unrecognized runes: {unknown}')
        runes = [c for c in raw if c in lookup]
        if not runes:
            skipped.append(Path(path).stem)
            continue
        for coordinate, column in [('index', 0), ('prime', 1)]:
            values = [lookup[c][column] for c in runes]
            for order in range(1, 10):
                values = differences(values)
                if order < 2:
                    continue
                # A short prefix suffices when its gcd reaches one. Keep it
                # alongside the full differences for independently checkable evidence.
                g, prefix = 0, []
                for value in values:
                    g = gcd(g, value)
                    prefix.append(value)
                    if g == 1:
                        break
                full_gcd = reduce(gcd, values, 0)
                rows.append(dict(page=Path(path).stem, representation=coordinate,
                                 runes=len(runes), degree_bound=order-1, order=order,
                                 differences=values, gcd=full_gcd,
                                 prefix_witness=prefix,
                                 excluded_all_moduli_gt_one=full_gcd == 1))
    return dict(schema='liberpedia-polynomial-stream-bound-v1',
                scope='Archived LP2-00–55; alphabet runes only, headings retained, page boundaries kept; zero-based indices and literal GP prime values.',
                model='c[i] congruent to P(N+s*i) modulo m; integer-coefficient P of degree at most d, integer N and s, fixed integer m>1 per page; no further map or skipped positions.',
                theorem='For degree <=d, the (d+1)st forward differences vanish modulo m. Therefore m divides their integer gcd. Gcd 1 excludes every m>1; other gcds are only a necessary condition.',
                input_sha256={p: hashlib.sha256(b).hexdigest() for p,b in blobs.items()},
                skipped_empty_pages=skipped, checks=len(rows),
                excluded_checks=sum(r['excluded_all_moduli_gt_one'] for r in rows), rows=rows,
                limits='No unknown plaintext, polynomial keys, rational coefficients, degree >8, nonlinear output map, irregular clock, internal resets or other transcription is tested. No Lean verification is claimed for this implementation.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print(f"PASS: {result['excluded_checks']}/{result['checks']} page/representation/degree checks have gcd one")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
