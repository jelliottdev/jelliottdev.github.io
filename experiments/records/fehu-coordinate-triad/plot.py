"""Draw the three fixed-rule sums for every eligible Fehu start."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / 'results.json'
OUT = HERE / 'coordinate-scan.svg'


def draw():
    report = json.loads(DATA.read_text(encoding='utf-8'))
    rows = report['rows']
    targets = (3001, 2819, 2579)
    names = ('A · X at first origin', 'B · Y across seam', 'C · X at reset origin')
    colors = ('#365a72', '#9b6135', '#567559')
    left, right = 140, 900
    width = right - left
    lo, hi = 2000, 3900

    def x(start):
        return left + (start - 1) * width / (len(rows) - 1)

    def y(value, top):
        return top + (hi - value) * 148 / (hi - lo)

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1060 650" role="img" '
             'aria-labelledby="title desc">',
             '<title id="title">Three Fehu coordinate sums across 350 fixed starts</title>',
             '<desc id="desc">Each panel scans the same fixed 59-Fehu rule. At start 182, the three sums simultaneously equal 3001, 2819 and 2579. This plot does not account for how the rule and targets were selected.</desc>',
             '<rect width="1060" height="650" fill="#fffdf9"/>',
             '<text x="36" y="38" font-family="Georgia,serif" font-size="27" fill="#20282c">The reported Fehu-coordinate triad</text>',
             '<text x="36" y="65" font-family="Arial,sans-serif" font-size="15" fill="#536069">LP2-only · 59 Fehu per window · 350 complete starts · one exact ordered triad under this fixed rule</text>']
    for series in range(3):
        top = 95 + series * 170
        baseline = top + 148
        target_y = y(targets[series], top)
        path = ' '.join(f'{"M" if i == 0 else "L"}{x(row["start_fehu"]):.1f},{y(row["sums"][series], top):.1f}' for i, row in enumerate(rows))
        parts.extend([
            f'<text x="36" y="{top + 19}" font-family="Arial,sans-serif" font-size="16" font-weight="bold" fill="{colors[series]}">{names[series]}</text>',
            f'<line x1="{left}" y1="{baseline}" x2="{right}" y2="{baseline}" stroke="#c8c9c4"/>',
            f'<line x1="{left}" y1="{target_y:.1f}" x2="{right}" y2="{target_y:.1f}" stroke="#858b89" stroke-dasharray="5 5"/>',
            f'<path d="{path}" fill="none" stroke="{colors[series]}" stroke-width="1.4" stroke-linejoin="round"/>',
            f'<circle cx="{x(182):.1f}" cy="{y(targets[series], top):.1f}" r="6" fill="{colors[series]}" stroke="#fffdf9" stroke-width="2"/>',
            f'<text x="{right + 12}" y="{target_y + 4:.1f}" font-family="Arial,sans-serif" font-size="13" fill="#424c50">target {targets[series]}</text>',
        ])
    marker = x(182)
    parts.extend([
        f'<line x1="{marker:.1f}" y1="92" x2="{marker:.1f}" y2="585" stroke="#263a44" stroke-opacity=".42" stroke-width="1.5"/>',
        f'<text x="{marker + 9:.1f}" y="601" font-family="Arial,sans-serif" font-size="14" fill="#263a44">F182</text>',
        f'<text x="{left}" y="624" font-family="Arial,sans-serif" font-size="14" fill="#536069">F1</text>',
        f'<text x="{right}" y="624" text-anchor="end" font-family="Arial,sans-serif" font-size="14" fill="#536069">F350</text>',
        '<text x="575" y="644" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#536069">Window start in LP2 Fehu order</text>',
        '</svg>'])
    return '\n'.join(parts) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    svg = draw()
    if args.check:
        assert OUT.read_text(encoding='utf-8') == svg
        print('PASS: coordinate-scan.svg matches saved results')
    else:
        OUT.write_text(svg, encoding='utf-8', newline='\n')
