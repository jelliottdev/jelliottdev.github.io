"""Render lag-one distance under two declared shuffle controls."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
left, right = 500, 810
x0, span = 82, 680
bar_width = span * 10 / (right - left)
observed = data['observed']['lag_one_sum']
parts = ['''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 820 365" role="img" aria-labelledby="title desc">
<title id="title">Doublet-event distance under two shuffle controls</title>
<desc id="desc">The observed lag-one circular-distance sum is 734. It lies well beyond most global shuffles but inside the central range of shuffles that preserve each page's event inventory.</desc>
<rect width="820" height="365" fill="#fff"/>
<text x="24" y="30" font-family="system-ui" font-size="18" fill="#243f50">Doublet-event distance depends on the control</text>
<text x="24" y="51" font-family="system-ui" font-size="12" fill="#4d5860">Lag-one sum across 85 event pairs · 20,000 seeded shuffles per control</text>''']
for mode, baseline, color, label in (
    ('global', 179, '#7392a4', 'Shuffle all events'),
    ('within_page', 303, '#637e69', 'Shuffle within pages')):
    histogram = {int(k): v for k, v in data['controls'][mode]['lag_one_sum_histogram'].items()}
    bins = {n: sum(count for value, count in histogram.items() if n <= value < n + 10)
            for n in range(left, right, 10)}
    peak = max(bins.values())
    parts.append(f'<text x="24" y="{baseline-88}" font-family="system-ui" font-size="13" fill="#243f50">{label}</text>')
    for n, count in bins.items():
        x = x0 + (n - left) * span / (right - left)
        h = 72 * count / peak
        parts.append(f'<rect x="{x:.2f}" y="{baseline-h:.2f}" width="{bar_width-1:.2f}" height="{h:.2f}" fill="{color}"/>')
    parts.append(f'<line x1="{x0}" y1="{baseline}" x2="{x0+span}" y2="{baseline}" stroke="#6e777b"/>')
obs_x = x0 + (observed - left) * span / (right - left)
parts.append(f'<line x1="{obs_x:.2f}" y1="76" x2="{obs_x:.2f}" y2="304" stroke="#ad4d39" stroke-width="2"/>')
parts.append(f'<text x="{obs_x+5:.2f}" y="73" font-family="system-ui" font-size="12" fill="#883c2c">Observed: {observed}</text>')
for tick in range(500, 801, 50):
    x = x0 + (tick - left) * span / (right - left)
    parts.append(f'<text x="{x:.2f}" y="329" text-anchor="middle" font-family="system-ui" font-size="11" fill="#4d5860">{tick}</text>')
parts.append('<text x="422" y="352" text-anchor="middle" font-family="system-ui" font-size="12" fill="#4d5860">Sum of minimum circular GP distances</text></svg>\n')
(HERE / 'shuffle-controls.svg').write_text('\n'.join(parts), encoding='utf-8', newline='\n')
