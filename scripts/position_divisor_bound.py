"""Audit fixed divisor labels of arithmetic-progression positions.

At each occurrence i of rune r require q[r] > 1 to divide N+s*i.
No label injectivity or primality is assumed. Gcd-one occurrence gaps
exclude unit strides and force q[r] to divide s for any other stride.
"""
import argparse
import hashlib
import json
from itertools import combinations
from math import gcd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/position-divisor-bound.json'


def report():
    paths = ['data/index.json'] + [f'text/lp2-{i:02}.txt' for i in range(56)]
    blobs = {p: (ROOT / p).read_bytes() for p in paths}
    alphabet = json.loads(blobs[paths[0]])['alphabet']
    labels = {a['rune']: a['latin'] for a in alphabet}
    rows, skipped = [], []
    for path in paths[1:]:
        raw = blobs[path].decode('utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - labels.keys()
        if unknown:
            raise ValueError(f'Unknown runes: {unknown}')
        stream = [c for c in raw if c in labels]
        if not stream:
            skipped.append(Path(path).stem)
            continue
        details = []
        for rune, label in labels.items():
            positions = [i for i,c in enumerate(stream) if c == rune]
            if not positions:
                continue
            g = 0
            for i in positions[1:]:
                g = gcd(g, i - positions[0])
            triple = next((list(t) for t in combinations(positions, 3)
                           if gcd(t[1]-t[0], t[2]-t[0]) == 1), None)
            details.append(dict(rune=rune, label=label, positions=positions,
                                gap_gcd=g, triple_witness=triple))
        rows.append(dict(page=Path(path).stem, rune_count=len(stream), runes=details,
                         gcd_one_labels=[d['label'] for d in details if d['gap_gcd']==1],
                         excludes_unit_stride=any(d['gap_gcd']==1 for d in details)))
    return dict(schema='liberpedia-position-divisor-bound-v1',
                scope='Archived LP2-00–55, alphabet runes only, headings retained, zero-based within-page positions; nonrunes do not advance the clock.',
                model='For each rune r a fixed integer q[r]>1 divides N+s*i at every occurrence i; arbitrary integer origin N and fixed integer stride s per page. Labels need not be prime, distinct or GP values.',
                theorem='If same-rune occurrence gaps have gcd 1, its divisor q must divide s. Thus s=1 or -1 is impossible; any stride coprime to that q is impossible. Noncoprime strides are not generally excluded.',
                input_sha256={p:hashlib.sha256(b).hexdigest() for p,b in blobs.items()},
                pages=rows, skipped_empty_pages=skipped,
                excluded_unit_stride_pages=sum(r['excludes_unit_stride'] for r in rows),
                limits='Necessary divisibility only; does not claim to decode a page or validate a deterministic factor-selection encoder. Changing labels, skipped positions, reset clocks, transformed output and noncoprime strides are not generally excluded. No formal proof assistant was run.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print(f"PASS: unit-stride contradiction on {result['excluded_unit_stride_pages']} pages")
    else:
        print(json.dumps(result,ensure_ascii=False,indent=2))
