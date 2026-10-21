"""Enumerate a toy sign-choice decoder; not a Liber Primus experiment."""
from itertools import product
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def enumerate_choices(shifts):
    return [dict(signs=list(signs), output=[(10 + sign * shift) % 29
                 for sign, shift in zip(signs, shifts)])
            for signs in product((-1, 1), repeat=len(shifts))]


def build():
    rows = enumerate_choices((1, 2, 3))
    zero_rows = enumerate_choices((1, 0, 3))
    unique = lambda records: len({tuple(row['output']) for row in records})
    assert len(rows) == unique(rows) == 8
    assert len(zero_rows) == 8 and unique(zero_rows) == 4
    # Recover each sign from its output rather than trusting the enumeration count.
    for row in rows:
        assert [(out - 10) % 29 for out in row['output']] == [
            (sign * shift) % 29 for sign, shift in zip(row['signs'], (1, 2, 3))]
    data = dict(scope='Toy mathematical illustration, not a manuscript test.',
                modulus=29, ciphertext=[10, 10, 10], shifts=[1, 2, 3],
                configurations=len(rows), distinct_outputs=unique(rows), rows=rows,
                zero_shift_comparison=dict(shifts=[1, 0, 3], configurations=8,
                                           distinct_outputs=unique(zero_rows), rows=zero_rows))
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 550" role="img" aria-labelledby="title desc">',
           '<title id="title">Three choices produce eight candidates</title>',
           '<desc id="desc">Ciphertext indices 10 10 10, with a choice of subtracting or adding shifts 1, 2 and 3 modulo 29. All eight sign combinations and their outputs are displayed. Replacing the middle shift with zero reduces distinct outputs to four.</desc>',
           '<rect width="360" height="550" fill="white"/>',
           '<style>text{font:15px Arial,sans-serif;fill:#253d49}.head{font-weight:bold}.small{font-size:13px}</style>',
           '<text x="16" y="28" class="head">Three choices → eight candidates</text>',
           '<text x="16" y="55">Input: 10, 10, 10 · modulus 29</text>',
           '<text x="16" y="87">10 ± 1</text><text x="130" y="87">10 ± 2</text><text x="244" y="87">10 ± 3</text>',
           '<path d="M87 82 H118 M201 82 H232" stroke="#637987" stroke-width="2"/>',
           '<text x="16" y="119" class="small">2 prefixes → 4 prefixes → 8 full outputs</text>',
           '<text x="22" y="156" class="head">Chosen operations</text>',
           '<text x="218" y="156" class="head">Output indices</text>']
    for i, row in enumerate(rows):
        y = 181 + i * 34
        if i % 2 == 0:
            svg.append(f'<rect x="12" y="{y-18}" width="336" height="32" fill="#eef2f4"/>')
        choices = '   '.join(('−' if sign < 0 else '+') + str(shift)
                             for sign, shift in zip(row['signs'], (1, 2, 3)))
        values = ', '.join(map(str, row['output']))
        svg.extend([f'<text x="22" y="{y}">{choices}</text>',
                    f'<text x="230" y="{y}">{values}</text>'])
    svg.extend(['<text x="16" y="468">With shifts 1, 0, 3 instead:</text>',
                '<text x="16" y="491">8 choices, but only 4 distinct outputs.</text>',
                '<text x="16" y="514" class="small">Adding zero and subtracting zero coincide.</text>',
                '<text x="16" y="539" class="small">Invented values; no manuscript claim.</text>', '</svg>'])
    (ROOT / 'exports/switching-choices-example.json').write_text(
        json.dumps(data, indent=2) + '\n', encoding='utf-8', newline='\n')
    (ROOT / 'exports/figures/switching-choices-example.svg').write_text(
        '\n'.join(svg) + '\n', encoding='utf-8', newline='\n')
    print('Verified 8 distinct sign-choice outputs and 4 distinct outputs with a zero shift.')


if __name__ == '__main__':
    build()
