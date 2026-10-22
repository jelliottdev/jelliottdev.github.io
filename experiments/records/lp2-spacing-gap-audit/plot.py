"""Small source-bound SVG diagram of the measured interline gaps."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def draw():
    d=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    rows={r['id']:r['measurements']['160']['blank_rows_between_lines'] for r in d['regions']}
    labels=[('LP2-15 number panel, row 1 → 2',rows['lp2-15-panel'][0],'#546c78'),
            ('LP2-15 number panel, row 2 → 3',rows['lp2-15-panel'][1],'#546c78'),
            ('LP2-15 number panel, row 3 → 4',rows['lp2-15-panel'][2],'#a6402b'),
            ('LP2-15 rune text (six gaps)',74,'#8e999c'),
            ('LP2-14 and LP2-16 rune text (17 gaps)',74,'#8e999c')]
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 450" role="img" aria-labelledby="title desc">',
         '<title id="title">LP2 line-gap measurement, original 2400-pixel-wide images</title>',
         '<desc id="desc">The LP2-15 number panel has 62, 61 and 79 blank-pixel rows between its four rows. The last gap is 17 pixels wider than either earlier panel gap. Adjacent text controls measure 73 to 75 pixels.</desc>',
         '<rect width="760" height="450" fill="#faf9f5"/>',
         '<text x="32" y="43" font-family="Georgia,serif" font-size="25" fill="#172b32">A wide gap before the fourth number row</text>',
         '<text x="32" y="68" font-family="Arial,sans-serif" font-size="14" fill="#49575c">Blank rows between printed line boxes · original JPEG pixels</text>']
    for i,(label,value,color) in enumerate(labels):
        y=112+i*57
        out.extend([f'<text x="32" y="{y}" font-family="Arial,sans-serif" font-size="15" fill="#25363d">{label}</text>',
                    f'<rect x="32" y="{y+9}" width="{value*7}" height="15" fill="{color}"/>',
                    f'<text x="{48+value*7}" y="{y+22}" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="{color}">{value} px</text>'])
    out.extend(['<text x="32" y="408" font-family="Arial,sans-serif" font-size="13" fill="#59666a">Text controls: LP2-15 = 74 px throughout; LP2-14/16 = 73–75 px.</text>',
                '<text x="32" y="428" font-family="Arial,sans-serif" font-size="13" fill="#59666a">This establishes a layout difference, not an encoded bit or its cause.</text>',
                '</svg>'])
    return '\n'.join(out)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    path=HERE/'line-gaps.svg'
    svg=draw()
    if args.check:
        assert path.read_text(encoding='utf-8')==svg
        print('PASS: line-gap figure reproduces')
    else:
        path.write_text(svg,encoding='utf-8')
        print(path)


if __name__=='__main__':
    main()
