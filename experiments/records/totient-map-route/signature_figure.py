"""Draw signature classes; check algebraic key counts, not reachable map nodes."""
import argparse
from collections import defaultdict
from itertools import product
import json
from math import gcd, prod
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / 'exports/figures/totient-signature-classes.svg'


def mobius(n):
    factors = 0
    for divisor in range(2, n + 1):
        if n % divisor:
            continue
        n //= divisor
        factors += 1
        if n % divisor == 0:
            return 0
        if n == 1:
            break
    return (-1) ** factors


def draw():
    groups = defaultdict(list)
    for k in range(1, 29):
        totient = sum(gcd(k, j) == 1 for j in range(1, k + 1))
        groups[mobius(totient)].append(k)
    assert [len(groups[v]) for v in (-1, 0, 1)] == [3, 16, 9]
    report = json.loads((ROOT / 'exports/totient-map-route.json').read_text(encoding='utf-8'))
    for row in report['signature_candidates']:
        sig = row['signature']
        expected = prod(len(groups[v]) for v in sig)
        assert sum(1 for _ in product(*(groups[v] for v in sig))) == expected
        assert expected == row['ordered_positive_index_triples']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="430" viewBox="0 0 360 430" role="img" aria-labelledby="title desc">',
             '<title id="title">A signature class does not identify a key</title>',
             '<desc id="desc">Indices 1 through 28 group by mu of phi of k. Class zero has 16 indices, minus one has 3, plus one has 9. Ordered triple counts multiply these sizes. These are not counts of reachable map nodes.</desc>',
             '<rect width="360" height="430" fill="white"/><g font-family="Arial,sans-serif" fill="#243d4a">',
             '<text x="12" y="23" font-size="17" font-weight="bold">Group key indices by μ(φ(k))</text>',
             '<text x="12" y="45" font-size="13">Derived key indices k = 1,…,28; F = 0 excluded</text>']
    for i, v in enumerate((0, -1, 1)):
        y = 62 + i * 76
        parts.append(f'<rect x="12" y="{y}" width="336" height="66" fill="#edf2f4"/>')
        parts.append(f'<text x="22" y="{y+21}" font-size="14" font-weight="bold">Class {v:+d}: {len(groups[v])} indices</text>')
        values = groups[v]
        for j, start in enumerate(range(0, len(values), 9)):
            text = ', '.join(map(str, values[start:start+9]))
            parts.append(f'<text x="22" y="{y+41+j*17}" font-size="13">{text}</text>')
    parts += ['<text x="12" y="310" font-size="15" font-weight="bold">Ordered keys with a given signature</text>',
              '<text x="12" y="337" font-size="15">(0, 0, 0): 16 × 16 × 16 = 4,096</text>',
              '<text x="12" y="362" font-size="15">(1, 0, 1): 9 × 16 × 9 = 1,296</text>',
              '<text x="12" y="394" font-size="13">These counts ignore node geometry and routes.</text>',
              '<text x="12" y="414" font-size="13">Matching a signature alone does not choose a key.</text>',
              '</g></svg>']
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate instead of checking the SVG')
    args = parser.parse_args()
    svg = draw()
    if args.write:
        OUTPUT.write_text(svg, encoding='utf-8', newline='\n')
    else:
        assert OUTPUT.read_text(encoding='utf-8') == svg, 'Signature figure differs'
    print('PASS: all six recorded signature counts and diagram')
