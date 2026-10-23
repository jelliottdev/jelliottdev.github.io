"""Compact, mobile-readable summary of source P08 key results."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
def build():
    r=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
    d=json.loads((HERE/"diagnostic-results.json").read_text(encoding="utf-8"))
    lp1=sum(x["gate"] for x in r["sweep"] if x["page"].startswith("lp1"))
    lp2=sum(x["gate"] for x in r["sweep"] if x["page"].startswith("lp2"))
    assert (lp1,lp2)==(99,4)
    maxnull=max(x["max_ioc"] for x in d["null"])
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 335" role="img" aria-labelledby="title desc">
<title id="title">P08 hint-grid key sweep: where the threshold hits occur</title>
<desc id="desc">Ninety-nine IoC threshold hits occur on solved LP1 pages and four on unsolved LP2 pages. Three LP2 hits reflect the same key relation. The top LP2 IoC is 1.382 versus the largest of 199 shuffled-page maxima, {maxnull:.3f}. This subset diagnostic was chosen after results were inspected.</desc>
<rect width="340" height="335" fill="#f4f5f6"/>
<g font-family="Arial, sans-serif" fill="#202a30">
<text x="16" y="29" font-size="17" font-weight="700">Where did the hits occur?</text>
<text x="16" y="51" font-size="13">Source IoC cutoff: above 1.25</text>
<text x="16" y="87" font-size="14">Solved LP1 pages</text>
<rect x="16" y="96" width="270" height="19" fill="#dfe4e7"/>
<rect x="16" y="96" width="270" height="19" fill="#667d8b"/>
<text x="322" y="111" font-size="14" font-weight="700" text-anchor="end">99</text>
<text x="16" y="146" font-size="14">Unsolved LP2 pages</text>
<rect x="16" y="155" width="270" height="19" fill="#dfe4e7"/>
<rect x="16" y="155" width="11" height="19" fill="#285e78"/>
<text x="322" y="170" font-size="14" font-weight="700" text-anchor="end">4</text>
<text x="16" y="204" font-size="14">3 of 4 LP2 hits share one relation.</text>
<line x1="16" x2="324" y1="222" y2="222" stroke="#c8d1d5"/>
<text x="16" y="250" font-size="15" font-weight="700">Top LP2 score: 1.382</text>
<text x="16" y="273" font-size="13">Highest shuffled score: {maxnull:.3f}</text>
<text x="16" y="299" font-size="13">199 shared page shuffles</text>
<text x="16" y="318" font-size="13">LP2-only check selected afterward</text>
</g></svg>'''

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--check",action="store_true");a=p.parse_args()
    val=build();dest=HERE/"comparison.svg"
    if a.check:
        assert dest.read_text(encoding="utf-8")==val
        print("PASS SVG")
    else:
        dest.write_text(val,encoding="utf-8",newline="\n")
        print(hashlib.sha256(val.encode()).hexdigest())
