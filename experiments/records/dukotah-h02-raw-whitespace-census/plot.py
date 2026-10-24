"""Show the preservation finding and the isolated signature control."""
import argparse
import json
from pathlib import Path
H = Path(__file__).resolve().parent

def render():
 r=json.loads((H/'results.json').read_text())
 check=json.loads((H/'independent-check.json').read_text())
 different=sum(g['trailing_whitespace_differs'] for g in check['canonical_variant_groups'])
 return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 520" role="img" aria-labelledby="title desc">
<title id="title">The signature does not settle trailing whitespace</title>
<desc id="desc">Copies in {different} canonical message groups differ in trailing-whitespace counts. In one isolated control, the original and a copy with an added space and tab both verify under the same key.</desc>
<rect width="560" height="520" fill="white"/>
<g font-family="Arial,sans-serif" fill="#20262c">
<text x="24" y="37" font-size="25" font-weight="bold">Same signed text, different endings</text>
<text x="24" y="76" font-size="23">{different} of {r['canonical_unique_bodies']} message groups have copies</text>
<text x="24" y="107" font-size="23">with different trailing-whitespace counts.</text>
<path d="M24 129H536" stroke="#d7dce0"/>
<text x="24" y="168" font-size="22" font-weight="bold">One GnuPG control</text>
<rect x="24" y="188" width="512" height="83" fill="#f1f3f5"/>
<text x="40" y="220" font-size="22">Archived copy before edit</text>
<text x="40" y="250" font-size="21" fill="#315e74">Signature valid</text>
<path d="M280 280V303m-9-10 9 10 9-10" stroke="#687780" stroke-width="2" fill="none"/>
<rect x="24" y="315" width="512" height="83" fill="#f1f3f5"/>
<text x="40" y="347" font-size="22">Same body + one space and one tab</text>
<text x="40" y="377" font-size="21" fill="#315e74">Same signature still valid</text>
<text x="24" y="438" font-size="21">Cleartext signatures ignore trailing spaces</text>
<text x="24" y="467" font-size="21">and tabs. Preserve original file bytes.</text>
<text x="24" y="503" font-size="19">One edited control; no claim of an intentional payload.</text>
</g></svg>'''

if __name__=='__main__':
 parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
 data=render()
 if args.check:
  assert (H/'census.svg').read_text(encoding='utf8')==data
  print('PASS: measured whitespace groups and control figure')
 else: (H/'census.svg').write_text(data,encoding='utf8',newline='\n')
