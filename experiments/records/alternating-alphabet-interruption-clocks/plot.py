"""Draw the two clock rules with a shared example, without raster screenshots."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="310" viewBox="0 0 360 310" role="img" aria-labelledby="title desc">',
         '<title id="title">An F can pause the key, or both clocks</title>',
         '<desc id="desc">A twelve-position example places F at positions three, four and ten. Both policies pause the selected key there. The first switches alphabet anyway; the second keeps the same alphabet for the next rune. All runes, including F, are decoded.</desc>',
         '<rect width="360" height="310" fill="white"/>',
         '<g font-family="Arial,Helvetica,sans-serif" fill="#20262b">',
         '<text x="12" y="26" font-size="18" font-weight="600">One marker, two clock rules</text>',
         '<text x="12" y="48" font-size="13">F pauses the selected key in both versions.</text>']
trace = data['clock_example']['key-only']
for i, step in enumerate(trace):
    x = 12 + i * 28
    if step['marker']:
        parts.append(f'<rect x="{x}" y="65" width="26" height="172" fill="#e9f0f5"/>')
    parts.append(f'<text x="{x+13}" y="82" text-anchor="middle" font-size="11" fill="#555f66">{i+1}</text>')
    parts.append(f'<text x="{x+13}" y="106" text-anchor="middle" font-size="14">{"F" if step["marker"] else "·"}</text>')
for policy, label, y in [('key-only', 'Pause key; switch alphabet', 133),
                         ('both', 'Pause key and alphabet', 195)]:
    parts.append(f'<text x="12" y="{y}" font-size="14" font-weight="600">{label}</text>')
    for i, step in enumerate(data['clock_example'][policy]):
        x = 12 + i * 28
        parts.append(f'<text x="{x+13}" y="{y+26}" text-anchor="middle" font-size="15" font-weight="600" fill="#285c79">{"AB"[step["alphabet"]]}</text>')
parts += ['<text x="12" y="262" font-size="14">A = GP order; B = reversed GP order.</text>',
          '<text x="12" y="285" font-size="13">Blue columns mark F. Every rune is decoded.</text>', '</g></svg>']
svg = '\n'.join(parts) + '\n'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
args = parser.parse_args()
path = HERE / 'clocks.svg'
if args.check:
    assert path.read_text(encoding='utf-8') == svg
else:
    path.write_text(svg, encoding='utf-8', newline='\n')
