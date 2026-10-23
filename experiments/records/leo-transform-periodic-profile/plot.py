"""Render a compact, responsive diagnostic from the pinned result file."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))['selected_section_control']
null = sorted(r['null_max_z'])
points = [('Shuffle median', null[len(null)//2], '#657785'),
          ('Shuffle 95th', null[474], '#657785'),
          ('Source peak', r['observed']['z'], '#27506a'),
          ('Planted cycle', r['planted_periodic_control']['z'], '#9a5e42')]
lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 270" role="img" aria-labelledby="title desc">',
         '<title id="title">Selected periodic score and the planted positive control</title>',
         '<desc id="desc">The source peak has z 5.95, compared with shuffle median 4.02 and 95th percentile 5.03. A strong planted 13-cycle selects the multiple 143, but scored z 3.51, below most shuffle maxima.</desc>',
         '<rect width="340" height="270" fill="#f3f5f6"/>',
         '<text x="16" y="29" font-family="Arial,sans-serif" font-size="17" font-weight="bold" fill="#24323a">Period found; score unconvincing</text>',
         '<text x="16" y="51" font-family="Arial,sans-serif" font-size="13" fill="#46535a">Highest z over five transforms and periods</text>']
for i, (label, value, color) in enumerate(points):
    y = 82 + i * 44
    width = round(145 * value / 6.2, 1)
    lines.extend([f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#24323a">{label}</text>',
                  f'<rect x="141" y="{y-12}" width="{width}" height="16" fill="{color}"/>',
                  f'<text x="{min(301, 147+width)}" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#24323a">{value:.2f}</text>'])
lines.extend(['<text x="16" y="252" font-family="Arial,sans-serif" font-size="13" fill="#46535a">499 within-section rune shuffles</text>', '</svg>'])
(HERE / 'periodic-profile.svg').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print('wrote periodic-profile.svg')
