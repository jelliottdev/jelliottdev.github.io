"""Deterministic, narrow fallback for the recorded control comparison."""
import argparse,json
from pathlib import Path
H=Path(__file__).resolve().parent
def svg():
    d=json.loads((H/'control-summary.json').read_bytes());k=d['known_key'];w=d['whole_search']
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="360" height="670" viewBox="0 0 360 670" role="img" aria-labelledby="title desc">
<title id="title">Passing a score is not recovering the text</title>
<desc id="desc">All {k['total']} known-key tests passed the English score, but only {k['exact_recoveries']} completely recovered their reading. Three of four full keyword searches recovered the complete reading. None of the 619,080 manuscript screens passed the first gate.</desc>
<rect width="360" height="670" fill="white"/>
<g font-family="Arial,sans-serif" fill="#242424" font-size="22">
<text x="20" y="35" font-weight="bold">A passing score can be wrong</text>
<text x="20" y="77">617 known-key tests</text>
<text x="20" y="113">English-score passes</text>
<rect x="20" y="129" width="320" height="24" fill="#666"/>
<text x="20" y="183">617 of 617</text>
<text x="20" y="230">Complete readings recovered</text>
<rect x="20" y="246" width="320" height="24" fill="#eee"/>
<rect x="20" y="246" width="{320*k['exact_recoveries']/k['total']:.6f}" height="24" fill="#666"/>
<text x="20" y="300">575 of 617</text>
<text x="20" y="340">42 passing outputs were wrong.</text>
<text x="20" y="379">These tests reuse two passages.</text>
<path d="M20 404H340" stroke="#aaa"/>
<text x="20" y="442" font-weight="bold">Complete 623-key searches</text>
<text x="20" y="479">{w['exact_recoveries']} of {w['total']} recovered the full reading.</text>
<path d="M20 503H340" stroke="#aaa"/>
<text x="20" y="542" font-weight="bold">Actual manuscript scan</text>
<text x="20" y="580">0 of 619,080 screens passed.</text>
<text x="20" y="617">No full-page decode was run.</text>
<text x="20" y="652">This does not exclude the cipher.</text>
</g></svg>'''
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=H/'control-recovery.svg';data=(svg()+'\n').encode('utf8')
    if a.check:assert out.read_bytes()==data;print('PASS: SVG matches saved controls')
    else:out.write_bytes(data)
