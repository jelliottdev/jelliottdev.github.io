"""Draw a narrow-screen comparison of full-search best scores."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent


def render(data):
    real=data['real']['best']['score']
    controls=[item['best_score'] for item in data['null_controls']]
    median=statistics.median(controls)
    known=data['positive_controls']['plant_score']
    threshold=-5.0
    low=-8.0; high=-4.0
    x=lambda v: round(70+(v-low)/(high-low)*270,2)
    vals=[('LP2 best',real,'#285873'),('Shuffle median',median,'#7f919b'),('Known reading',known,'#293b49')]
    dots=''.join(f'<circle cx="{x(v)}" cy="150" r="3.4" fill="#9caeb8" opacity=".72"/>' for v in controls)
    rows=''.join(f'<text x="17" y="{195+i*31}" font-size="13" fill="#27333a">{label}</text><circle cx="155" cy="{190+i*31}" r="7" fill="{color}"/><text x="345" y="{195+i*31}" text-anchor="end" font-size="13" fill="#27333a">{val:.3f}</text>' for i,(label,val,color) in enumerate(vals))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 315" role="img" aria-labelledby="t d">
<title id="t">Whole-search scores for reading-direction routes</title>
<desc id="d">LP2 best {real:.3f}; shuffle median {median:.3f}; known direct reading {known:.3f}. Higher scores look more like English under this model.</desc>
<rect width="360" height="315" fill="#f4f6f7"/>
<text x="17" y="29" font-family="Arial,sans-serif" font-size="18" font-weight="bold" fill="#27333a">Reading-direction search</text>
<text x="17" y="53" font-family="Arial,sans-serif" font-size="13" fill="#4b5b64">Higher = more English-like under this model</text>
<g font-family="Arial,sans-serif"><line x1="70" y1="102" x2="340" y2="102" stroke="#87949b" stroke-width="1.5"/>
<line x1="{x(threshold)}" y1="88" x2="{x(threshold)}" y2="163" stroke="#6b7880" stroke-dasharray="4 4"/>
<text x="{x(threshold)-4}" y="80" text-anchor="end" font-size="13" fill="#4b5b64">Source score bar −5</text>
<text x="70" y="122" text-anchor="middle" font-size="13" fill="#4b5b64">−8</text><text x="205" y="122" text-anchor="middle" font-size="13" fill="#4b5b64">−6</text><text x="340" y="122" text-anchor="middle" font-size="13" fill="#4b5b64">−4</text>
<circle cx="{x(known)}" cy="150" r="7" fill="#293b49"/>{dots}<circle cx="{x(real)}" cy="150" r="8" fill="#285873" stroke="white" stroke-width="2"/>
{rows}
<text x="17" y="295" font-size="13" fill="#4b5b64">49 complete shuffled searches, same grid</text></g>
</svg>\n'''


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
    s=render(json.loads((HERE/'results.json').read_text(encoding='utf8')))
    f=HERE/'comparison.svg'
    if a.check:
        assert f.read_text(encoding='utf8')==s
        print('PASS SVG')
    else:
        f.write_text(s,encoding='utf8',newline='\n')
        print('Saved',f)
