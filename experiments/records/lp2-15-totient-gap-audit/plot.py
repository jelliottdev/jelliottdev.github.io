"""Render every LP2-15 source-array step and the two unresolved distinctions."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="636" viewBox="0 0 1080 636" role="img" aria-labelledby="t d">',
        '<title id="t">Audit of the reported LP2-15 totient and Fibonacci-gap arrays</title>',
        '<desc id="d">All sixteen printed panel entries are shown with their reported prime candidates, zero-based prime indices and proposed Fibonacci gaps. The red 3299 is changed to 3298 by Euler totient. Cells 4,1 and 4,2 require addition instead of the reported subtraction label. Cell 4,1 reports gap 317 where the arithmetic gives 377. Cell 2,2 is a question mark in the source.</desc>',
        '<rect width="1080" height="636" fill="#faf9f6"/>',
        '<text x="28" y="42" font-family="Georgia,serif" font-size="27" fill="#1e303a">A second route through the number panel</text>',
        '<text x="28" y="68" font-family="Arial,sans-serif" font-size="15" fill="#4b5d66">Printed cell → prime-only φ → 3301 ± value → zero-based prime index → reported gap</text>',
    ]
    for cell in result['cells']:
        row, col = cell['row'], cell['column']
        x, y = 28 + (col-1)*258, 92 + (row-1)*121
        special = (row, col) == (4, 1)
        fill = '#f8eadf' if special else ('#eaf0ed' if cell['printed_is_prime'] else '#ffffff')
        parts.append(f'<rect x="{x}" y="{y}" width="245" height="109" fill="{fill}" stroke="#b8c4c9"/>')
        p = cell['printed']
        q = cell['calculated_post_totient']
        text = f'{p} → φ {q}' if p != q else str(p)
        ink = '#9b362e' if cell['printed_is_prime'] else '#1e303a'
        parts.append(f'<text x="{x+13}" y="{y+26}" font-family="Arial,sans-serif" font-size="20" font-weight="600" fill="{ink}">{text}</text>')
        chosen = next(s for s in cell['sign_options'] if s['source_selected'])
        sign = '3301 − x' if chosen['sign'] == '-' else '3301 + x'
        parts.append(f'<text x="{x+13}" y="{y+52}" font-family="Arial,sans-serif" font-size="15" fill="#36536a">{sign} = {cell["source_prime_candidate"]}</text>')
        index = cell['source_candidate_prime_index']
        gap = '?' if cell['source_gap'] is None else str(cell['source_gap'])
        label = f'index {index} · gap {gap}' if not special else f'index 987 · 317 ≠ 377'
        parts.append(f'<text x="{x+13}" y="{y+78}" font-family="Arial,sans-serif" font-size="14" fill="{"#a0402c" if special else "#526069"}">{label}</text>')
        parts.append(f'<text x="{x+218}" y="{y+25}" font-family="Arial,sans-serif" font-size="11" fill="#7c8b90">{row},{col}</text>')
    parts += [
        '<line x1="28" x2="1052" y1="590" y2="590" stroke="#bdc8ca"/>',
        '<text x="28" y="615" font-family="Arial,sans-serif" font-size="14" fill="#4b5d66">The posted gap list has 14 of 15 specified cells consistent with this predecessor calculation; one cell is uncertain.</text>',
        '</svg>',
    ]
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    svg = build()
    if args.check:
        assert svg == (HERE / 'panel-audit.svg').read_text(encoding='utf-8')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(svg)
    print('Source-array audit figure reproduces.')


if __name__ == '__main__':
    main()
