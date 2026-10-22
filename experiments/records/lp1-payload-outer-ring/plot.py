"""Draw the exact extracted borders and their common interior."""
import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / 'four-borders-one-interior.svg'


def render():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="514" viewBox="0 0 1220 514" role="img" aria-labelledby="title desc">',
             '<title id="title">Four signed LP1 diagrams retain the same interior after perimeter removal</title>',
             '<desc id="desc">LP1-10, LP1-11, LP1-12 and LP1-13 use outer digits 3, 3, 0 and 1. Removing those outer rows and side digits leaves the same three by three number matrix in original orientation.</desc>',
             '<rect width="1220" height="514" fill="#fbfaf7"/>',
             '<text x="30" y="43" font-family="Georgia,serif" font-size="26" fill="#172e3a">Four message diagrams, one interior</text>',
             '<text x="30" y="70" font-family="Arial,sans-serif" font-size="14" fill="#4b5960">Orange digits are removed; the interior is retained without rotation or reflection.</text>']
    char_width = 10.9
    for i, n in enumerate(range(10, 14)):
        page = f'lp1-{n:02}'
        row = result['four_signed_message_diagrams'][page]
        x = 30 + 300 * i
        parts += [f'<rect x="{x}" y="92" width="280" height="310" rx="4" fill="#fff" stroke="#ced5d7"/>',
                  f'<text x="{x+15}" y="123" font-family="Arial,sans-serif" font-weight="700" font-size="16" fill="#193b4d">{page.upper()}</text>',
                  f'<text x="{x+218}" y="123" font-family="Arial,sans-serif" font-size="13" fill="#965324">edge {row["border_digit"]}</text>']
        dx = x + 16
        for r, line in enumerate(row['printed_lines']):
            y = 163 + 33 * r
            common = f'font-family="Consolas,monospace" font-size="18" xml:space="preserve"'
            if r in (0, 6):
                parts.append(f'<text x="{dx}" y="{y}" {common} fill="#a75a2c">{html.escape(line)}</text>')
            else:
                parts += [f'<text x="{dx}" y="{y}" {common} fill="#a75a2c">{line[0]}</text>',
                          f'<text x="{dx+char_width}" y="{y}" {common} fill="#193b4d">{html.escape(line[1:-1])}</text>',
                          f'<text x="{dx+15*char_width}" y="{y}" {common} fill="#a75a2c">{line[-1]}</text>']
    parts += ['<rect x="30" y="420" width="1160" height="70" rx="4" fill="#e7eff1"/>',
              '<text x="46" y="447" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#193b4d">Retained in every message</text>',
              '<text x="46" y="473" font-family="Consolas,monospace" font-size="17" fill="#193b4d">10  12  10   /   12  14  12   /   10  12  10</text>',
              '<text x="900" y="472" font-family="Arial,sans-serif" font-size="13" fill="#4b5960">Row sums: 32, 38, 32</text>',
              '</svg>']
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    svg = render()
    if args.check:
        assert TARGET.read_text(encoding='utf-8') == svg
        print('PASS: figure matches checked result')
    else:
        TARGET.write_text(svg, encoding='utf-8')
        print(TARGET)


if __name__ == '__main__':
    main()
