"""Phone-width comparison of the three declared grid-byte readings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROWS = [('archived','Archived'),('canon','Six cells checked'),('resolved','Eleven cells checked')]


def render(results):
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="360" height="379" viewBox="0 0 360 379" role="img" aria-labelledby="title desc">',
        '<title id="title">Three readings of the grid bytes, two fixed screens</title>',
        '<desc id="desc">The best printable-byte fraction is 45.2 to 46.2 percent, below the source 85 percent flag. The best index-based English score is minus 7.339 to minus 7.183, below the source minus 5 threshold.</desc>',
        '<rect width="360" height="379" fill="#f7f8fa"/>',
        '<text x="16" y="26" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202a33">Do the corrected cells change the result?</text>',
        '<text x="16" y="57" font-family="Arial,sans-serif" font-size="14" font-weight="600" fill="#202a33">Best printable-byte fraction</text>',
        '<text x="16" y="77" font-family="Arial,sans-serif" font-size="13" fill="#45535f">Source flag: more than 85%</text>',
    ]
    for i,(key,label) in enumerate(ROWS):
        y = 106 + i*48
        value = results['witnesses'][key]['ciphertext']['best']['printable']*100
        width = round(219*value/100,2)
        out += [f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#202a33">{label}</text>',
                f'<rect x="16" y="{y+8}" width="219" height="12" rx="2" fill="#dce3e8"/>',
                f'<rect x="16" y="{y+8}" width="{width}" height="12" rx="2" fill="#426780"/>',
                f'<text x="246" y="{y+19}" font-family="Arial,sans-serif" font-size="14" fill="#202a33">{value:.1f}%</text>']
    out += ['<path d="M16 248 H344" stroke="#cbd4db"/>',
            '<text x="16" y="270" font-family="Arial,sans-serif" font-size="14" font-weight="600" fill="#202a33">Best rune-index reading</text>',
            '<text x="16" y="290" font-family="Arial,sans-serif" font-size="13" fill="#45535f">Source English-score bar: above −5.0</text>']
    for i,(key,label) in enumerate(ROWS):
        y = 315 + i*19
        winner = max(results['witnesses'][key]['index'].values(),key=lambda x:x['score'])['score']
        out += [f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#202a33">{label}</text>',
                f'<text x="262" y="{y}" font-family="Arial,sans-serif" font-size="14" fill="#202a33">{winner:.3f}</text>']
    out += ['</svg>']
    return '\n'.join(out)+'\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args = parser.parse_args()
    content = render(json.loads((HERE/'results.json').read_text(encoding='utf-8')))
    path = HERE/'comparison.svg'
    if args.check:
        assert path.read_text(encoding='utf-8') == content
        print('PASS figure matches three saved witnesses')
    else:
        path.write_text(content,encoding='utf-8',newline='\n')
        print(path)
