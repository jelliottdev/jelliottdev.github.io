"""Render a compact explanatory result figure from the saved sweep."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / 'source/analysis/round12/C1/results.json').read_text())
control = json.loads((HERE / 'controls.json').read_text())
best = d['top20'][0]['score']
bar = d['hit_bar']
x0, x1 = -8.0, -3.8
left, width = 180, 455
x = lambda n: left + (n - x0) / (x1 - x0) * width
lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 730 220" role="img" aria-labelledby="t d">',
    '<title id="t">Feedback sweep scores</title>',
    '<desc id="d">The planted English control clears the required score. The best of 23,520 LP2 configurations remains below it.</desc>',
    '<rect width="730" height="220" fill="#fff"/>',
    '<style>text{font:14px system-ui,sans-serif;fill:#273039}.small{font-size:12px;fill:#5b646b}</style>'
]
for label, score, color, y in [
    ('Planted control', control['english_score'], '#316681', 40),
    ('Best LP2 candidate', best, '#738893', 95),
    ('Required score', bar, '#38464f', 150),
]:
    lines += [f'<text x="14" y="{y+5}">{label}</text>',
              f'<line x1="{left}" y1="{y}" x2="{left+width}" y2="{y}" stroke="#e0e4e6" stroke-width="7"/>',
              f'<circle cx="{x(score):.1f}" cy="{y}" r="8" fill="{color}"/>',
              f'<text x="{left+width+14}" y="{y+5}">{score:.3f}</text>']
for tick in (-8, -7, -6, -5, -4):
    lines.append(f'<text class="small" x="{x(tick):.1f}" y="196" text-anchor="middle">{tick}</text>')
lines += ['<text class="small" x="180" y="214">Lower</text>',
          '<text class="small" x="635" y="214" text-anchor="end">Higher English score →</text>', '</svg>']
(HERE / 'scores.svg').write_text('\n'.join(lines)+'\n',encoding='utf-8')
