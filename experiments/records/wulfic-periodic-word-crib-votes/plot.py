"""Visual explanation of the source vote/held-out control distinction."""
import argparse,json
from pathlib import Path
P=Path(__file__).resolve().parent
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    s=json.loads((P/'summary.json').read_text(encoding='utf-8'))
    plants=json.loads((P/'plants.json').read_text(encoding='utf-8'))
    all_plants=[f for row in plants for f in row['folds']]
    assert all(f['hits']<=11 and f['eligible']>=29 for f in all_plants)
    assert all(f['hits']==0 for f in s['observed_folds'])
    svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 344" role="img" aria-labelledby="t d">
<title id="t">A crib-voted key must predict words it did not use</title>
<desc id="d">The source votes on half the word slots to form a periodic key. None of the untouched LP2 slots become exact source-dictionary words. The same test recovers at most 11 of roughly 30 untouched words from known planted messages, failing its positive control.</desc>
<rect width="340" height="344" fill="#f4f6f8"/>
<g font-family="Arial, sans-serif" fill="#202a32">
<text x="18" y="30" font-size="18" font-weight="700">Can the key predict new words?</text>
<rect x="18" y="49" width="304" height="67" rx="5" fill="#e4ebf0"/>
<text x="34" y="76" font-size="15" font-weight="700">1. Use half the word slots</text>
<text x="34" y="100" font-size="14">Vote for a 17- or 43-value key.</text>
<path d="M170 118v22m-5-5 5 5 5-5" fill="none" stroke="#516777" stroke-width="2"/>
<rect x="18" y="145" width="304" height="76" rx="5" fill="#e4ebf0"/>
<text x="34" y="173" font-size="15" font-weight="700">2. Check untouched slots</text>
<text x="34" y="199" font-size="15">LP2: 0 exact words in every fold.</text>
<path d="M170 223v22m-5-5 5 5 5-5" fill="none" stroke="#516777" stroke-width="2"/>
<rect x="18" y="251" width="304" height="66" rx="5" fill="#d6e4ec"/>
<text x="34" y="279" font-size="15" font-weight="700">Known-message control also fails</text>
<text x="34" y="303" font-size="14">At most 11 of about 30 words recovered.</text>
<text x="18" y="338" font-size="13" fill="#4c5c66">This cannot exclude periodic-key ciphers.</text>
</g></svg>\n'''
    p=P/'heldout.svg'
    if a.check: assert p.read_text(encoding='utf-8')==svg
    else:p.write_text(svg,encoding='utf-8',newline='\n')
if __name__=='__main__':main()
