"""Draw the measured gap distributions at mobile legibility."""
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
rows=json.loads((HERE/'results.json').read_text(encoding='utf8'))['regions']
parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 300" role="img" aria-labelledby="t d">',
       '<title id="t">Four page-region gap measurements</title>',
       '<desc id="d">Ordinary blank-row gaps are 73–75 pixels. The selected reported big-gap pages each have one larger gap: 109, 110 and 129 pixels. The comparison page has no larger gap in the tested region.</desc>',
       '<rect width="360" height="300" fill="#f7f8f9"/>',
       '<text x="16" y="29" font-family="system-ui,sans-serif" font-size="17" font-weight="650" fill="#24343d">Blank rows between rune lines</text>',
       '<text x="16" y="49" font-family="system-ui,sans-serif" font-size="11" fill="#536570">Each dot is one measured interline gap.</text>']
for i,r in enumerate(rows):
    y=92+i*49
    gaps=r['measurements']['160']['blank_rows_between']
    parts.append(f'<text x="16" y="{y}" font-family="system-ui,sans-serif" font-size="13" font-weight="650" fill="#24343d">{r["page"].upper()}</text>')
    parts.append(f'<path d="M95 {y-5}H302" stroke="#becbd1"/>')
    for j,g in enumerate(gaps):
        x=95+(g-70)*3.3
        offset=(j%3-1)*3
        color='#a44739' if g>=100 else '#31566e'
        parts.append(f'<circle cx="{x:.1f}" cy="{y-5+offset}" r="3.5" fill="{color}"/>')
    large=[g for g in gaps if g>=100]
    parts.append(f'<text x="337" y="{y}" text-anchor="end" font-family="system-ui,sans-serif" font-size="13" fill="#24343d">{max(large) if large else "none"}</text>')
parts += ['<text x="95" y="271" font-family="system-ui,sans-serif" font-size="11" fill="#536570">70</text>',
          '<text x="206" y="271" font-family="system-ui,sans-serif" font-size="11" fill="#536570">105</text>',
          '<text x="282" y="271" font-family="system-ui,sans-serif" font-size="11" fill="#536570">130 px</text>',
          '<text x="16" y="291" font-family="system-ui,sans-serif" font-size="10" fill="#536570">Four fixed crops; no whole-book gap census.</text>','</svg>']
payload='\n'.join(parts)+'\n';out=HERE/'gap-measurements.svg'
if args.check:assert out.read_text(encoding='utf8')==payload
else:out.write_text(payload,encoding='utf8')
print('Gap figure checked.' if args.check else 'Gap figure written.')
