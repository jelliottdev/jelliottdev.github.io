"""Enumerate every within-page eleven-rune prime sum in LP2-27 through LP2-32.

This is a descriptive census, not a random-model significance test.
Run from any directory; --check compares the complete stored report.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/wing-tree-windows.json'


def report():
    paths = ['data/index.json'] + [f'text/lp2-{n:02}.txt' for n in range(27, 33)]
    inputs = {p: (ROOT / p).read_bytes() for p in paths}
    alphabet = json.loads(inputs[paths[0]])['alphabet']
    values = {a['rune']: a['prime'] for a in alphabet}
    pages = []
    for path in paths[1:]:
        raw = inputs[path].decode('utf-8')
        unknown = {c for c in raw if '\u16a0' <= c <= '\u16ff'} - values.keys()
        if unknown:
            raise ValueError(f'Unknown runes: {unknown}')
        cells = [(offset, c) for offset, c in enumerate(raw) if c in values]
        primes = [values[c] for _, c in cells]
        prefix = [0]
        for p in primes:
            prefix.append(prefix[-1] + p)
        windows = []
        for start in range(len(cells) - 10):
            total = prefix[start + 11] - prefix[start]
            # Independent direct summation catches offset/end-point mistakes.
            assert total == sum(primes[start:start + 11])
            windows.append(dict(start_rune=start + 1, end_rune=start + 11,
                                source_start=cells[start][0],
                                source_end_inclusive=cells[start + 10][0],
                                runes=''.join(c for _, c in cells[start:start + 11]),
                                prime_sum=total))
        pages.append(dict(page=Path(path).stem, rune_count=len(cells),
                          window_count=len(windows),
                          hit_counts={str(t): sum(w['prime_sum'] == t for w in windows)
                                      for t in (563, 569)},
                          window_sum_total=sum(w['prime_sum'] for w in windows),
                          windows=windows))
    count = sum(p['window_count'] for p in pages)
    total = sum(p['window_sum_total'] for p in pages)
    return dict(input_sha256={p: hashlib.sha256(b).hexdigest() for p, b in inputs.items()},
                scope='LP2-27–32, eleven consecutive alphabet runes, forward order, all starting positions within each page; headings retained, separators removed; no page crossing, wrapping, reversal or padding.',
                index_convention='Rune positions one-based; source offsets zero-based Unicode character offsets in UTF-8-decoded archived text.',
                targets=[563, 569], pages=pages, window_count=count,
                window_sum_total=total, mean_window_sum=total / count,
                hit_counts={str(t): sum(p['hit_counts'][str(t)] for p in pages) for t in (563, 569)},
                limitation='Targets and section were selected after the reported correspondence. Overlapping windows share ten runes. Frequencies are descriptive, not independent trials or p-values; this does not test unspecified grid layouts or manuscript-row claims.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: all eleven-rune windows, coordinates, sums and input hashes')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
