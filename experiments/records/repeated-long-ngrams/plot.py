"""Draw a compact, responsive SVG of selected repeat-count control tails."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
d = json.loads((here/'results.json').read_text(encoding='utf-8'))
rows = [('Five-rune repeats', d['null_at_least_observed']['5'], '#58758b'),
        ('Six-rune repeats', d['null_at_least_observed']['6'], '#58758b'),
        ('Either length', d['any_5_or_6_at_least_observed'], '#315d77')]
parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 234" role="img" aria-labelledby="title desc">',
         '<title id="title">Repeated long rune sequences under section-matched controls</title>',
         '<desc id="desc">Of 999 controls, 300 matched the five-rune count, 150 matched the six-rune count, and 361 matched either.</desc>',
         '<rect width="360" height="234" fill="#f3f5f6"/>',
         '<text x="18" y="27" font-family="system-ui,sans-serif" font-size="16" font-weight="700" fill="#172a34">How often controls match the count</text>',
         '<text x="18" y="45" font-family="system-ui,sans-serif" font-size="11" fill="#4e626e">999 section-matched step shuffles · LP2-00–55</text>']
for i, (label, value, color) in enumerate(rows):
    y = 69 + i*52
    parts.extend([f'<text x="18" y="{y}" font-family="system-ui,sans-serif" font-size="12" fill="#172a34">{label}</text>',
                  f'<rect x="18" y="{y+8}" width="267" height="15" fill="#dce3e7"/>',
                  f'<rect x="18" y="{y+8}" width="{267*value/999:.2f}" height="15" fill="{color}"/>',
                  f'<text x="294" y="{y+21}" font-family="system-ui,sans-serif" font-size="12" font-weight="700" fill="#172a34">{value}</text>'])
parts.append('<text x="18" y="223" font-family="system-ui,sans-serif" font-size="11" fill="#4e626e">A larger bar means a less exceptional finding.</text></svg>')
(here/'repeats.svg').write_text('\n'.join(parts)+'\n', encoding='utf-8', newline='\n')
