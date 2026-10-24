import argparse,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=json.loads((HERE/'results.json').read_text());x=lambda score:70+(score+8)*115
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="440" viewBox="0 0 600 440" role="img" aria-labelledby="title desc">
<title id="title">Does moving the grid key help?</title><desc id="desc">Thirty thousand one hundred twelve short checks selected234 complete-page decodes. None passed the source English-score bar. The strongest complete output scored minus6.361 on LP2-49, below minus5.5. Higher means more English four-letter patterns, not a verified reading.</desc>
<rect width="600" height="440" fill="white"/><g font-family="Arial, sans-serif" fill="#222">
<text x="24" y="41" font-size="27" font-weight="bold">Does moving the grid key help?</text>
<text x="24" y="79" font-size="21">30,112 short checks → 234 full-page decodes</text>
<text x="24" y="124" font-size="21">Strongest complete output: LP2-49</text>
<line x1="70" y1="242" x2="530" y2="242" stroke="#777" stroke-width="2"/>
<line x1="{x(r['best_full']['score']):.3f}" y1="151" x2="{x(r['best_full']['score']):.3f}" y2="242" stroke="#444" stroke-width="5"/>
<text x="{x(r['best_full']['score'])-20:.3f}" y="184" font-size="22" text-anchor="end">−6.361</text>
<line x1="{x(-5.5):.3f}" y1="151" x2="{x(-5.5):.3f}" y2="242" stroke="#888" stroke-width="2" stroke-dasharray="6 5"/>
<text x="{x(-5.5)+12:.3f}" y="171" font-size="21">Score bar</text><text x="{x(-5.5)+12:.3f}" y="204" font-size="21">−5.5</text>
{''.join(f'<line x1="{x(v)}" y1="242" x2="{x(v)}" y2="249" stroke="#777"/><text x="{x(v)}" y="278" font-size="20" text-anchor="middle">{str(v).replace("-","−")}</text>' for v in [-8,-7,-6,-5,-4])}
<text x="300" y="315" text-anchor="middle" font-size="20">Higher = more English four-letter patterns</text>
<text x="24" y="363" font-size="24" font-weight="bold">No complete output cleared the bar.</text>
<text x="24" y="400" font-size="20">Four grid-derived keys; bounded starting phases.</text>
<text x="24" y="428" font-size="20">A good score alone would not prove a reading.</text></g></svg>'''
 p=HERE/'payload-phases.svg'
 if args.check:assert p.read_text(encoding='utf-8')==svg;print('PASS deterministic SVG')
 else:p.write_text(svg,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
