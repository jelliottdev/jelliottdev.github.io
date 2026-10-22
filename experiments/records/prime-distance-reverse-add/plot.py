"""Create a compact, source-derived chart of the 53 paired digit sums."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
values = data['paired_sums']
assert len(values) == 53 and values == values[::-1]
width, left, base, scale, step = 920, 46, 190, 13, 15.5
bars = []
for i, value in enumerate(values):
    x = left + i * step
    y = base - value * scale
    fill = '#315c79' if i < 26 else '#9a6845' if i > 26 else '#66747b'
    bars.append(f'<rect x="{x:.1f}" y="{y}" width="11.5" height="{value * scale}" fill="{fill}"/>')
    if i in (0, 12, 25, 26, 27, 40, 52):
        bars.append(f'<text x="{x + 5.75:.1f}" y="211" text-anchor="middle" font-size="12">{i+1}</text>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 235" role="img" aria-labelledby="title desc">
<title id="title">Paired digit sums in the reported 53-digit reverse-add example</title>
<desc id="desc">Fifty-three bars are mirror-symmetric. All values range from zero to seven, below the carry threshold of ten. The left and right halves use different colors to show their reflection.</desc>
<rect width="100%" height="100%" fill="#fff"/>
<line x1="46" x2="864" y1="60" y2="60" stroke="#a34d3d" stroke-width="1.5" stroke-dasharray="6 4"/>
<text x="866" y="56" font-size="13" fill="#713b30">carry at 10</text>
<line x1="46" x2="864" y1="190" y2="190" stroke="#6a747b"/>
{''.join(bars)}
<text x="46" y="227" font-size="13" fill="#4c555c">String position</text>
</svg>'''
(HERE / 'paired-sums.svg').write_text(svg + '\n', encoding='utf-8', newline='\n')
print('Wrote paired-sums.svg from stored arithmetic results')
