"""Mobile chart of the held-out raw-reader controls."""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / 'solved-reader-gate.svg'


def render():
    d = json.loads((HERE / 'gate-results.json').read_text(encoding='utf-8'))
    rows = d['solved_page_controls']
    assert len(rows) == 2 and not d['overall']['pass']
    bars = []
    for y, row in zip((88, 155), rows):
        length = 270 * row['agreement']
        gate_x = 24 + 270 * 0.9
        bars.append(f'''<text x="24" y="{y}" fill="#263d4c" font-size="15" font-weight="700">{row['page'].upper()}</text>
<text x="294" y="{y}" text-anchor="end" fill="#30424e" font-size="14">{row['matched']}/{row['compared']} = {row['agreement']:.1%}</text>
<rect x="24" y="{y+11}" width="270" height="22" fill="#e7ecef"/>
<rect x="24" y="{y+11}" width="{length:.2f}" height="22" fill="#557c8d"/>
<line x1="{gate_x:.2f}" y1="{y+6}" x2="{gate_x:.2f}" y2="{y+40}" stroke="#292f34" stroke-width="2"/>''')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 264" role="img" aria-labelledby="t d" style="font-family:Arial,sans-serif">
<title id="t">The fresh ornament reader misses its solved-page gate</title>
<desc id="d">Raw reading matched 82 of 96 glyphs on LP2-56 and 89 of 109 on LP2-57. Both are below the source's 90 percent gate.</desc>
<rect width="320" height="264" fill="#fff"/>
<text x="24" y="29" fill="#222b33" font-size="17" font-weight="700">Can the reader read known text?</text>
<text x="24" y="53" fill="#4b5962" font-size="13">Held-out solved pages · no text-position hints</text>
{''.join(bars)}
<text x="24" y="218" fill="#263d4c" font-size="14" font-weight="700">Combined: {d['overall']['agreement']:.1%}</text>
<text x="24" y="241" fill="#4b5962" font-size="13">Black marks show the required 90%.</text>
</svg>'''


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    svg = render()
    if args.check:
        assert OUT.read_text(encoding='utf-8') == svg
    else:
        OUT.write_text(svg, encoding='utf-8', newline='\n')
    print(OUT.name)
