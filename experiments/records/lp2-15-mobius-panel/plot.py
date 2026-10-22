"""Draw the printed LP2-15 values and calculated Mobius values together."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    cells = result['cells']
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="512" viewBox="0 0 760 512" role="img" aria-labelledby="t d">',
        '<title id="t">Möbius values of the LP2-15 printed panel</title>',
        '<desc id="d">The sixteen printed numbers are shown in their original four-by-four order. Below each number is the calculated arithmetic Möbius value. All outputs are zero except the second row, which reads minus one, minus one, minus one, plus one.</desc>',
        '<rect width="760" height="512" fill="#f9f8f4"/>',
        '<text x="28" y="40" font-family="Georgia,serif" font-size="25" fill="#17252e">The printed panel, transformed</text>',
        '<text x="28" y="67" font-family="Arial,sans-serif" font-size="15" fill="#4b5b62">LP2-15 · each cell shows printed number above calculated μ(n)</text>',
    ]
    for cell in cells:
        r, c, n, value = (cell[key] for key in ('row', 'column', 'printed', 'mobius'))
        x = 28 + (c - 1) * 181
        y = 90 + (r - 1) * 94
        fill = '#e6edf0' if value == 0 else ('#d8e8db' if value == 1 else '#e4e0ef')
        ink = '#9b332a' if n == 3299 else '#17252e'
        parts.extend([
            f'<rect x="{x}" y="{y}" width="167" height="82" rx="3" fill="{fill}" stroke="#afb9bd"/>',
            f'<text x="{x + 15}" y="{y + 30}" font-family="Arial,sans-serif" font-size="24" fill="{ink}">{n}</text>',
            f'<text x="{x + 15}" y="{y + 62}" font-family="Arial,sans-serif" font-size="19" fill="#526168">μ = {"−1" if value == -1 else value}</text>',
            f'<text x="{x + 136}" y="{y + 30}" font-family="Arial,sans-serif" font-size="12" fill="#75858b">{r},{c}</text>',
        ])
    parts.extend([
        '<line x1="28" x2="732" y1="472" y2="472" stroke="#b9c2c2"/>',
        '<text x="28" y="497" font-family="Arial,sans-serif" font-size="14" fill="#4b5b62">12 square-factor zeros · 3 values of −1 · 1 value of +1</text>',
        '</svg>',
    ])
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    svg = build()
    if args.check:
        if svg != (HERE / 'panel.svg').read_text(encoding='utf-8'):
            raise SystemExit('Stored figure differs from recomputation')
        print('Figure reproduces from the saved 16-cell ledger.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(svg)


if __name__ == '__main__':
    main()
