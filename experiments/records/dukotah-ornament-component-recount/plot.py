"""Compare the count fields without treating components as glyphs."""
import argparse,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def render():
 r=json.loads((HERE/'results.json').read_bytes())
 assert r['summary']=={'bands':30,'pages':19,'matches_stored':30,'matches_reported':9,'exceeds_16':13,'fresh_range':[0,341]}
 return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 450" role="img" aria-labelledby="title desc">
<title id="title">Thirty ornament boxes, counted from their original ink</title>
<desc id="desc">Fresh counts match all 30 saved component counts, but only nine original n values. Thirteen boxes exceed sixteen components. Components are not glyphs.</desc>
<rect width="560" height="450" fill="white"/>
<g font-family="Arial,sans-serif" fill="#20262c">
<text x="24" y="36" font-size="25" font-weight="bold">What did the small-box filter select?</text>
<text x="24" y="72" font-size="21">30 boxes selected by the old n ≤ 16 field</text>
<text x="24" y="122" font-size="22">Fresh ink count matches saved component count</text>
<rect x="24" y="143" width="420" height="27" fill="#315e74"/>
<text x="458" y="165" font-size="22">30/30</text>
<text x="24" y="222" font-size="22">Fresh ink count matches the old n field</text>
<rect x="24" y="243" width="126" height="27" fill="#7b8992"/>
<text x="164" y="265" font-size="22">9/30</text>
<text x="24" y="327" font-size="24" font-weight="bold">13 boxes exceed 16 components.</text>
<text x="24" y="362" font-size="22">The filter did not mean “at most 16 glyphs.”</text>
<path d="M24 386H536" stroke="#d7dce0"/>
<text x="24" y="421" font-size="20">Ink regions are not glyph names or hidden messages.</text>
</g></svg>'''

if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
 data=render()
 if args.check:
  assert (HERE/'component-counts.svg').read_text(encoding='utf8')==data
  print('PASS: component-count figure')
 else: (HERE/'component-counts.svg').write_text(data,encoding='utf8',newline='\n')
