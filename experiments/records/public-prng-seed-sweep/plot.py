"""A compact source-result comparison, with values read from the replay output."""

import json
from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "source/analysis/round16/prng/results.json").read_text())
scores = [("Planted control", d["ctrl_score"], "#316681"),
          ("Best manuscript candidate", d["best_score"], "#798995"),
          ("Required score", d["effective_bar"], "#37424a")]
x0, x1 = -8.0, -3.8
left, width = 190, 450
pos = lambda x: left + (x - x0) / (x1 - x0) * width
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 232" role="img" aria-labelledby="title desc">',
         '<title id="title">PRNG screen: best candidate below required score</title>',
         '<desc id="desc">The planted control scores above the threshold; the strongest of 52,556 manuscript decodes remains below it. Higher scores are better.</desc>',
         '<rect width="720" height="232" fill="#fff"/>',
         '<style>text{font:14px system-ui,sans-serif;fill:#24292d}.small{font-size:12px;fill:#59636a}</style>']
for i, (label, score, color) in enumerate(scores):
    y = 42 + i * 55
    parts += [f'<text x="16" y="{y+5}">{escape(label)}</text>',
              f'<line x1="{left}" x2="{left+width}" y1="{y}" y2="{y}" stroke="#dce0e2" stroke-width="8"/>',
              f'<circle cx="{pos(score):.1f}" cy="{y}" r="8" fill="{color}"/>',
              f'<text x="{left+width+13}" y="{y+5}">{score:.3f}</text>']
for tick in (-8, -7, -6, -5, -4):
    x = pos(tick)
    parts += [f'<text class="small" x="{x:.1f}" y="211" text-anchor="middle">{tick}</text>']
parts += ['<text class="small" x="190" y="226">Lower</text>',
          '<text class="small" x="639" y="226" text-anchor="end">Higher English score →</text>',
          '</svg>']
(HERE / 'score.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8')
