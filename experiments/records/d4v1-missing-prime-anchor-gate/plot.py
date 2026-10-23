"""Phone-readable control-gate figure from the complete saved results."""
import argparse
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def render():
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    a,b=result['key_controls']
    assert a['null_pass_count']==b['null_pass_count']==199
    route=result['route_control']
    assert route['null_pass_count']==199
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 229" role="img" aria-labelledby="title desc">
<title id="title">Shuffled controls pass the source score threshold</title>
<desc id="desc">On one 157-rune known-reading fixture, all 199 shuffled controls pass the source's 0.91 unigram score line for each of its two keys after scanning Atbash shifts. Route order cannot change unigram fitness.</desc>
<rect width="340" height="229" fill="#f3f5f6"/>
<g font-family="Arial,sans-serif" fill="#263f54">
<text x="16" y="29" font-size="17" font-weight="700">The source score passes shuffles</text>
<text x="16" y="53" font-size="13">One 157-rune known-reading control</text>
<text x="16" y="83" font-size="14">256-pair key</text>
<rect x="16" y="94" width="230" height="16" rx="3" fill="#54798c"/>
<text x="254" y="108" font-size="14" font-weight="700">199/199</text>
<text x="16" y="136" font-size="14">Missing-prime key</text>
<rect x="16" y="147" width="230" height="16" rx="3" fill="#54798c"/>
<text x="254" y="161" font-size="14" font-weight="700">199/199</text>
<path d="M16 181H324" stroke="#c5ced4"/>
<text x="16" y="204" font-size="14" font-weight="700">Route order cannot change this score.</text>
<text x="16" y="221" font-size="13">Similar rune counts do not prove a reading.</text>
</g></svg>
'''

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    svg=render();path=HERE/'control-screen.svg'
    if args.check:
        assert path.read_text(encoding='utf-8')==svg
        print('PASS: control figure matches complete results')
    else:path.write_text(svg,encoding='utf-8',newline='\n')
