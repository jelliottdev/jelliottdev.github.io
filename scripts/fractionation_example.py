"""A nine-symbol coordinate example, not a proposed Liber Primus cipher."""
from itertools import product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ALPHABET = 'ABCDEFGHI'


def encode(values):
    rows = [v // 3 for v in values]
    columns = [v % 3 for v in values]
    components = rows + columns
    return [3 * components[i] + components[i + 1]
            for i in range(0, len(components), 2)]


def decode(values):
    components = [part for value in values for part in divmod(value, 3)]
    n = len(values)
    return [3 * components[i] + components[n + i] for i in range(n)]


def build():
    checked = 0
    for length in range(1, 5):
        for values in product(range(9), repeat=length):
            assert decode(encode(values)) == list(values)
            assert encode(decode(values)) == list(values)
            checked += 1
    plain = [ALPHABET.index(c) for c in 'FACE']
    cipher = encode(plain)
    assert ''.join(ALPHABET[v] for v in cipher) == 'DBGH'
    split_cipher = encode(plain[:2]) + encode(plain[2:])
    assert ''.join(ALPHABET[v] for v in split_cipher) == 'DGBH'
    data = dict(scope='Invented coordinate example, not an LP experiment.',
                alphabet=ALPHABET, dimensions=[3, 3], input='FACE', output='DBGH',
                two_symbol_blocks_output='DGBH', row_components=[v // 3 for v in plain],
                column_components=[v % 3 for v in plain],
                both_round_trips_checked=checked, tested_lengths=[1, 2, 3, 4])
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 570" role="img" aria-labelledby="title desc">',
           '<title id="title">Split, rearrange and regroup coordinates</title>',
           '<desc id="desc">A three by three square labels rows and columns zero to two and places A through I in row order. FACE has rows 1 0 0 1 and columns 2 0 2 1. Joining rows then columns gives pairs 10, 01, 20, 21, which map to DBGH. This is an invented example.</desc>',
           '<rect width="360" height="570" fill="white"/>',
           '<style>text{font:16px Arial,sans-serif;fill:#253d49}.head{font-weight:bold}.small{font-size:13px}</style>',
           '<text x="16" y="27" class="head">Split, rearrange, regroup</text>']
    for c in range(3):
        svg.append(f'<text x="{114+c*54}" y="58">{c}</text>')
    for r in range(3):
        svg.append(f'<text x="69" y="{92+r*42}">{r}</text>')
        for c in range(3):
            x, y = 96 + c * 54, 65 + r * 42
            svg.extend([f'<rect x="{x}" y="{y}" width="54" height="42" fill="#eef2f4" stroke="#bdc9d0"/>',
                        f'<text x="{x+18}" y="{y+27}">{ALPHABET[3*r+c]}</text>'])
    lines = [(224, 'Input: F    A    C    E'),
             (255, 'Rows: 1    0    0    1'), (284, 'Cols:  2    0    2    1'),
             (326, 'Join rows, then columns:'), (355, '1 0 0 1  2 0 2 1'),
             (397, 'Regroup into coordinate pairs:'), (426, '(1,0)  (0,1)  (2,0)  (2,1)'),
             (468, 'Look up each pair: D  B  G  H')]
    svg.extend(f'<text x="20" y="{y}">{text}</text>' for y, text in lines)
    svg.extend(['<text x="20" y="513" class="small">Decode by splitting the paired coordinates</text>',
                '<text x="20" y="533" class="small">into equal row and column halves.</text>',
                '<text x="20" y="558" class="small">Invented alphabet; no manuscript claim.</text>', '</svg>'])
    (ROOT / 'exports/fractionation-example.json').write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8', newline='\n')
    (ROOT / 'exports/figures/fractionation-example.svg').write_text('\n'.join(svg)+'\n', encoding='utf-8', newline='\n')
    print(f'Checked both round trips for {checked} inputs of lengths 1–4; FACE encodes to DBGH.')


if __name__ == '__main__':
    build()
