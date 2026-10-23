"""Render the preregistered positive-control comparison as a small SVG."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))['rows']
labels = {'LATIN': 'Latin', 'GREEK': 'Greek', 'OLD_ENGLISH': 'Old English', 'ENOCHIAN': 'Enochian'}
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 388" role="img" aria-labelledby="t d">',
    '<title id="t">The four non-English controls tie at 100 percent power</title>',
    '<desc id="d">For each language, both the English and own-language models cleared their null maximum on all 24 planted texts. The frozen rule required the own-language model to exceed English.</desc>',
    '<rect width="320" height="388" fill="#f6f7f8"/>',
    '<g font-family="Arial, sans-serif" fill="#20292f">',
    '<text x="16" y="29" font-size="18" font-weight="700">Four ties, no strict win</text>',
    '<text x="16" y="52" font-size="13">The frozen rule required own-model power</text>',
    '<text x="16" y="69" font-size="13">to exceed English power.</text>',
]
for i, row in enumerate(rows):
    top = 88 + i * 67
    assert row['english_power'] == row['own_model_power'] == 1.0
    parts += [
        f'<text x="16" y="{top+15}" font-size="14" font-weight="700">{labels[row["register"]]}</text>',
        f'<text x="16" y="{top+34}" font-size="13">English</text>',
        f'<rect x="117" y="{top+21}" width="137" height="16" fill="#667f8a"/>',
        f'<text x="260" y="{top+34}" font-size="13">24/24</text>',
        f'<text x="16" y="{top+55}" font-size="13">Own model</text>',
        f'<rect x="117" y="{top+42}" width="137" height="16" fill="#315f78"/>',
        f'<text x="260" y="{top+55}" font-size="13">24/24</text>',
    ]
parts += [
    '<line x1="16" y1="360" x2="304" y2="360" stroke="#c6cdd0"/>',
    '<text x="16" y="379" font-size="13">Source control summary; no new LP2 decode.</text>',
    '</g></svg>\n',
]
svg = '\n'.join(parts)
path = HERE / 'control-gate.svg'
if '--check' in sys.argv:
    assert path.read_text(encoding='utf-8') == svg
    print('PASS: control-gate.svg matches results')
else:
    path.write_text(svg, encoding='utf-8', newline='\n')
    print('Wrote', path)
