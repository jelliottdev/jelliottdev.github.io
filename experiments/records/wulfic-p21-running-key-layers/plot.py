"""Small mobile-readable source-gate summary; no inferential p-values."""
import argparse
import json
import pathlib

HERE=pathlib.Path(__file__).resolve().parent

def svg():
    data=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    counts=data['target']['counts']
    assert counts=={'running':12327,'layered':12312}
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 238" role="img" aria-labelledby="title desc">
<title id="title">P21–30 running-key source gate</title>
<desc id="desc">All {counts['running']:,} direct and {counts['layered']:,} layered candidate decodings were below the source's coincidence threshold. Nine constructed controls and one post-target known-reading control pass.</desc>
<rect width="320" height="238" fill="#f5f6f7"/>
<g font-family="Arial, sans-serif" fill="#25343d">
<text x="16" y="30" font-size="18" font-weight="700">Source gate on LP2-04–13</text>
<text x="16" y="57" font-size="13">Normalized coincidence must exceed 1.3</text>
<line x1="16" y1="72" x2="304" y2="72" stroke="#b9c3c9"/>
<text x="16" y="98" font-size="14">Direct running key</text><text x="304" y="98" font-size="14" text-anchor="end">0 / {counts['running']:,}</text>
<text x="16" y="128" font-size="14">Keyword + running key</text><text x="304" y="128" font-size="14" text-anchor="end">0 / {counts['layered']:,}</text>
<line x1="16" y1="143" x2="304" y2="143" stroke="#b9c3c9"/>
<text x="16" y="169" font-size="14">Constructed readable controls</text><text x="304" y="169" font-size="14" text-anchor="end">9 / 9 pass</text>
<text x="16" y="197" font-size="14">Known-reading diagnostic</text><text x="304" y="197" font-size="14" text-anchor="end">1 / 1 passes</text>
<text x="16" y="225" font-size="12">Last row was checked after the target result.</text>
</g></svg>'''

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    output=HERE/'gate.svg';expected=svg()
    if a.check:assert output.read_text(encoding='utf8')==expected
    else:output.write_text(expected,encoding='utf8',newline='\n')
    print('PASS' if a.check else output)

if __name__=='__main__':main()
