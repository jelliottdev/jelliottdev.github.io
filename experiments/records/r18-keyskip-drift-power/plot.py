"""Render the pinned planted-key power result as a phone-width SVG."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render():
    d = json.loads((HERE / 'source-results.json').read_text(encoding='utf-8'))
    rows = d['B2']['rows']
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 420" role="img" aria-labelledby="title desc">',
           '<title id="title">Correct-key detection as windows grow</title>',
           '<desc id="desc">With a planted correct key, rigid detection drops from 70 percent at 25 runes to 0.5 percent at 400 runes. A skip-aware beam detects all 200 plants at each length. At full manuscript length, three planted keys are recovered at over 99.9 percent of rune positions.</desc>',
           '<rect width="320" height="420" fill="#f7f8fa"/>',
           '<text x="16" y="28" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#202c34">Can a correct key survive drift?</text>',
           '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#4e5e69">Planted-key detection · 200 trials per length</text>',
           '<text x="16" y="85" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">Runes</text>',
           '<text x="85" y="85" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">Rigid alignment</text>',
           '<text x="264" y="85" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">Beam</text>']
    for i, row in enumerate(rows):
        y = 115 + i * 39
        value = 100 * row['rigid_detect_power']
        out.append(f'<text x="17" y="{y+4}" font-family="Arial,sans-serif" font-size="13" fill="#26333c">{row["L"]}</text>')
        out.append(f'<rect x="84" y="{y-9}" width="167" height="17" fill="#e1e7eb"/>')
        out.append(f'<rect x="84" y="{y-9}" width="{167*value/100:.1f}" height="17" fill="#47687a"/>')
        out.append(f'<text x="{min(245, 89+167*value/100):.1f}" y="{y+4}" font-family="Arial,sans-serif" font-size="13" fill="#26333c">{value:g}%</text>')
        out.append(f'<text x="266" y="{y+4}" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#245770">{100*row["beam_detect_power"]:g}%</text>')
        if i < 5:
            out.append(f'<line x1="16" y1="{y+18}" x2="304" y2="{y+18}" stroke="#dce3e7"/>')
    full = d['B3'][-1]
    out.append('<line x1="16" y1="350" x2="304" y2="350" stroke="#bac8d0"/>')
    out.append('<text x="16" y="374" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#26333c">Full length · 12,956 runes</text>')
    out.append(f'<text x="16" y="395" font-family="Arial,sans-serif" font-size="13" fill="#4e5e69">Beam recovery: {100*full["mean_recovery"]:.2f}% across 3 plants</text>')
    out.append('</svg>')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    file = HERE / 'drift-power.svg'
    content = render()
    if args.check:
        assert file.read_text(encoding='utf-8') == content
        print('PASS: mobile SVG matches pinned source result')
    else:
        file.write_text(content, encoding='utf-8', newline='\n')


if __name__ == '__main__':
    main()
