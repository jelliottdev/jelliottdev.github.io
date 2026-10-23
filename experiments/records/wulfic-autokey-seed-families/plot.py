"""A compact source-screen diagram, with one row per method branch."""
import json
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
OUT = HERE/'screen.svg'
ROWS = (
    ('Named keywords','named_keywords'),
    ('Every two-rune seed','two_rune_seeds'),
    ('Every three-rune seed','three_rune_seeds'),
    ('P21–30 DEOR variant','distinct_p21_deor'),
)


def figure():
    data = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 350 394">',
        '<title id="title">Four archived autokey seed searches and their source-defined screens</title>',
        '<desc id="desc">Each row shows configurations tested, configurations passing the source singleton gate, and hits exceeding its index-of-coincidence threshold. All four methods have zero source hits. The DEOR variant has no singleton gate.</desc>',
        '<rect width="350" height="394" fill="#fff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#26343c;font-size:13px}.head{font-size:18px;font-weight:700}.label{font-size:14px;font-weight:700}.muted{fill:#536571}</style>',
        '<text x="16" y="27" class="head">The source search, in four branches</text>',
        '<text x="16" y="49" class="muted">One-rune words must decode to I or A.</text>',
    ]
    for index,(label,key) in enumerate(ROWS):
        row = data['observed'][key]
        y = 67 + index*75
        gate = 'No I/A word check' if key == 'distinct_p21_deor' else f"{row['gate_count']:,} pass I/A word check"
        parts.extend([
            f'<rect x="12" y="{y}" width="326" height="68" rx="3" fill="#f1f4f6" stroke="#d5dfe5"/>',
            f'<rect x="12" y="{y}" width="4" height="68" fill="#2e6681"/>',
            f'<text x="27" y="{y+21}" class="label">{escape(label)}</text>',
            f'<text x="27" y="{y+43}">{row["configurations"]:,} settings  ·  {escape(gate)}</text>',
            f'<text x="27" y="{y+61}" class="muted">{row["hit_count"]} above the source IoC threshold</text>',
        ])
    parts.extend([
        '<text x="16" y="379" class="muted">The screen checks IoC &gt; 1.3; a hit is not a reading.</text>',
        '</svg>',
    ])
    return '\n'.join(parts)+'\n'


def main():
    svg=figure()
    if '--check' in sys.argv:
        assert OUT.read_text(encoding='utf-8') == svg
    else:
        OUT.write_text(svg,encoding='utf-8',newline='\n')
    print('PASS: phone-readable screen diagram')


if __name__ == '__main__':
    main()
