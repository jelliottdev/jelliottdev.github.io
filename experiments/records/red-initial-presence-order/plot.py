"""Render a compact, original vector comparison of the tested page sequences."""

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
rows = [
    ('Total-red rule', result['source_total_red_pages'], '#35596d'),
    ('Large initials', result['corrected_pages'], '#35596d'),
    ('Even spacing control', result['controls']['approximately_even_pages'], '#6b7982'),
    ('Consecutive control', result['controls']['consecutive_pages'], '#6b7982'),
]

parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 288" role="img" aria-labelledby="title desc">',
    '<title id="title">LP2 pages with large red initials and two spacing controls</title>',
    '<desc id="desc">The total-red rule selects 15 pages, including two pages with small red text only. The corrected large-initial rule selects 13 pages. The same count is shown in approximately even and consecutive control arrangements.</desc>',
    '<rect width="860" height="288" fill="#f3f5f6"/>',
    '<text x="22" y="30" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#233440">One mark per LP2 page</text>',
]
left, step = 204, 10.55
for tick in (0, 10, 20, 30, 40, 50, 57):
    x = left + tick * step
    parts.append(f'<text x="{x:.1f}" y="60" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#52616b">{tick:02d}</text>')
for rowno, (label, selected, color) in enumerate(rows):
    y = 89 + rowno * 48
    parts.append(f'<text x="22" y="{y+5}" font-family="Arial,sans-serif" font-size="15" fill="#233440">{label}</text>')
    selected = set(selected)
    for page in range(58):
        x = left + page * step
        if rowno == 0 and page in (7, 53):
            fill = '#a8403c'
        elif page in selected:
            fill = color
        else:
            fill = '#d4dbe0'
        radius = 5.1 if page in selected else 3.5
        parts.append(f'<circle cx="{x:.1f}" cy="{y}" r="{radius}" fill="{fill}"/>')
parts.extend([
    '<rect x="22" y="262" width="11" height="11" fill="#a8403c"/>',
    '<text x="42" y="272" font-family="Arial,sans-serif" font-size="13" fill="#43535d">LP2-07 and LP2-53: small red text counted as large initials by the total-red rule</text>',
    '</svg>',
])
(HERE / 'page-order.svg').write_text(''.join(parts) + '\n', encoding='utf-8', newline='\n')
print('Saved page-order.svg')
