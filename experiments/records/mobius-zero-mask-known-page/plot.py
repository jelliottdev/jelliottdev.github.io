"""Render the declared comparison of 29 constant shifts as a compact SVG."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
bars = []
for row in data['shifts']:
    x = 66 + row['shift'] * 25
    h = row['total_mismatch'] * 3.3
    color = '#ae4c36' if row['shift'] == 1 else '#8ba6b6'
    bars.append(f'<rect x="{x}" y="{262-h}" width="17" height="{h}" fill="{color}"/>')
    if row['shift'] in (0, 1, 5, 10, 15, 20, 25, 28):
        bars.append(f'<text x="{x+8}" y="282" text-anchor="middle" font-size="12">{row["shift"]}</text>')
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 830 320" role="img" aria-labelledby="title desc">
<title id="title">Zero-mask mismatches across constant GP shifts</title>
<desc id="desc">Twenty-nine bars show mismatch counts for each fixed shift on LP2-56. The published minus-one shift is highlighted and has fifty mismatches. Shift zero has none by definition.</desc>
<rect width="830" height="320" fill="#fff"/>
<text x="24" y="28" font-family="system-ui" font-size="17" fill="#243f50">Zero-mask mismatches on LP2-56</text>
<text x="24" y="48" font-family="system-ui" font-size="12" fill="#4d5860">85 runes · ciphertext versus shifted reading · published shift 1 in red</text>
<line x1="57" y1="262" x2="800" y2="262" stroke="#68757d"/>
<line x1="57" y1="62" x2="57" y2="262" stroke="#68757d"/>
<text x="52" y="66" text-anchor="end" font-size="11">60</text>
<text x="52" y="264" text-anchor="end" font-size="11">0</text>
''' + '\n'.join(bars) + '''
<text x="425" y="310" text-anchor="middle" font-family="system-ui" font-size="12">Plaintext index = ciphertext index − shift (mod 29)</text>
</svg>\n'''
(HERE / 'mismatches.svg').write_text(svg, encoding='utf-8', newline='\n')
