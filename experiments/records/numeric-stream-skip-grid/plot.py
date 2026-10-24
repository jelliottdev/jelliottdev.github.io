import argparse,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=json.loads((HERE/'results.json').read_text());best=r['best_full']['score'];x=lambda s:70+(s+8)*115
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="600" height="420" viewBox="0 0 600 420" role="img" aria-labelledby="title desc">
<title id="title">Did a numeric key clear the score bar?</title><desc id="desc">36,300 short screens selected 322 complete-page checks. None cleared the source bar of minus5.5. The strongest complete output on LP2-49 scored minus6.412. Higher scores mean more English four-letter patterns, not proof of plaintext.</desc>
<rect width="600" height="420" fill="white"/><g font-family="Arial, sans-serif" fill="#222">
<text x="24" y="40" font-size="26" font-weight="bold">Did a numeric key clear the score bar?</text>
<text x="24" y="78" font-size="21">36,300 short screens → 322 full-page checks</text>
<text x="24" y="123" font-size="21">Source-selected maximum: LP2-49</text>
<line x1="70" y1="240" x2="530" y2="240" stroke="#777" stroke-width="2"/>
<line x1="{x(best):.3f}" y1="154" x2="{x(best):.3f}" y2="240" stroke="#444" stroke-width="5"/>
<text x="{x(best)-40:.3f}" y="184" font-size="22" text-anchor="end">−6.412</text>
<line x1="{x(-5.5):.3f}" y1="150" x2="{x(-5.5):.3f}" y2="240" stroke="#888" stroke-width="2" stroke-dasharray="6 5"/>
<text x="{x(-5.5)+12:.3f}" y="171" font-size="21">Score bar</text><text x="{x(-5.5)+12:.3f}" y="202" font-size="21">−5.5</text>
{''.join(f'<line x1="{x(v)}" y1="240" x2="{x(v)}" y2="247" stroke="#777"/><text x="{x(v)}" y="275" text-anchor="middle" font-size="20">{str(v).replace("-","−")}</text>' for v in [-8,-7,-6,-5,-4])}
<text x="300" y="312" text-anchor="middle" font-size="20">Higher = more English four-letter patterns</text>
<text x="24" y="359" font-size="24" font-weight="bold">0 of 322 full outputs cleared the bar.</text>
<text x="24" y="395" font-size="20">A good score alone does not establish a reading.</text></g></svg>'''
 target=HERE/'numeric-skip.svg'
 if args.check:assert target.read_text(encoding='utf-8')==svg;print('PASS deterministic figure')
 else:target.write_text(svg,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
