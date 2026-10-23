"""Mobile summary of distinct limitations and the selected score."""
import argparse
import json
import pathlib
HERE=pathlib.Path(__file__).resolve().parent

def svg():
    x=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    rows=[r for p in x['pages'] for r in p['rows']]
    target=max(r['word_score'] for r in rows)
    nulls=sorted(t['global_max_score'] for t in x['null'])
    ge=sum(n>=target for n in nulls)
    assert x['invariants']=={'full_length_ioc_cases':390,'word_order_score_cases':50,'subset_cases':60}
    assert target==111 and ge==85 and len(nulls)==199
    control=x['control']
    assert control['full_route_recovery'] and control['known_spaced_score']==1266
    assert control['known_flat_score']==control['source_reverse_route_score']==0
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 286" role="img" aria-labelledby="title desc">
<title id="title">Correct recovery, zero points</title>
<desc id="desc">The complete constructed 261-rune message was recovered exactly. Its source dictionary score is 1266 when word spaces are kept, but zero when the recovered runes are scored without spaces. On the manuscript, the top score of {target} was met or beaten by {ge} of 199 shuffled full searches.</desc>
<rect width="320" height="286" fill="#f5f6f7"/>
<g font-family="Arial, sans-serif" fill="#25343d">
<text x="16" y="28" font-size="18" font-weight="700">Correct recovery, zero points</text>
<text x="16" y="51" font-size="13">Constructed 261-rune control</text>
<text x="16" y="81" font-size="14">Word spaces kept</text>
<rect x="16" y="91" width="230" height="18" fill="#285e73"/>
<text x="304" y="105" font-size="14" text-anchor="end">1,266</text>
<text x="16" y="139" font-size="14">Same runes, spaces removed</text>
<line x1="16" y1="149" x2="246" y2="149" stroke="#b9c3c9"/>
<circle cx="16" cy="149" r="3" fill="#687d86"/>
<text x="304" y="154" font-size="14" text-anchor="end">0</text>
<text x="16" y="181" font-size="13">The scorer lost the word boundaries.</text>
<line x1="16" y1="202" x2="304" y2="202" stroke="#b9c3c9"/>
<text x="16" y="225" font-size="13">Manuscript: 450 routes on ten pages</text>
<text x="16" y="247" font-size="14">Highest word score: {target}</text>
<text x="16" y="269" font-size="13">{ge} / 199 shuffled searches scored as well.</text>
</g></svg>'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    p=HERE/'route-summary.svg';v=svg()
    if a.check:assert p.read_text(encoding='utf8')==v
    else:p.write_text(v,encoding='utf8',newline='\n')
    print('PASS' if a.check else p)
if __name__=='__main__':main()
