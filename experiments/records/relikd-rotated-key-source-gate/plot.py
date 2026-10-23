"""Phone-width view of the first source gate; all values verified in ioc-diagnostic."""
import argparse
import json
from pathlib import Path

H = Path(__file__).resolve().parent
CONTROL = json.loads((H / "control-results.json").read_text(encoding="utf8"))
DIAG = json.loads((H / "ioc-diagnostic.json").read_text(encoding="utf8"))
plant = CONTROL["true_model"]["ioc"]
target = DIAG["target_max_ioc"]
shuffled = max(DIAG["null_max_ioc"])
assert 1.6 < plant < 2.1 and target < 1.6 and shuffled < 1.6

def x(v):
    return 32 + (v - 1.0) * 310

def make():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 350" role="img" aria-labelledby="title desc">
<title id="title">Repaired source pattern screen stops before key fitting</title>
<desc id="desc">The known-reading plant reached normalized index of coincidence {plant:.2f} and passed the source gate above 1.6. The strongest LP2 setting reached {target:.2f}; the highest of 49 shuffled complete searches reached {shuffled:.2f}. Neither could enter source key fitting.</desc>
<rect width="320" height="350" fill="#f7f9fa"/>
<g font-family="Arial,sans-serif" fill="#172b39">
<text x="16" y="27" font-size="17" font-weight="700">The source screen stops here</text>
<text x="16" y="51" font-size="13">Mean column repeat score · higher is better</text>
<line x1="32" x2="280" y1="76" y2="76" stroke="#bac8cf"/>
<text x="27" y="69" font-size="13">1.0</text>
<text x="144" y="69" font-size="13">1.4</text>
<text x="258" y="69" font-size="13">1.8</text>
<line x1="{x(1.6):.1f}" x2="{x(1.6):.1f}" y1="78" y2="294" stroke="#a64f34" stroke-width="2"/>
<text x="{x(1.6)+7:.1f}" y="96" font-size="13" fill="#813a27">1.6 gate</text>
<text x="16" y="111" font-size="14" font-weight="700">Known-text plant</text>
<rect x="32" y="123" width="{x(plant)-32:.1f}" height="16" fill="#2e6678"/>
<text x="16" y="159" font-size="13">Passed · {plant:.2f}</text>
<text x="16" y="189" font-size="14" font-weight="700">Strongest LP2 setting</text>
<rect x="32" y="199" width="{x(target)-32:.1f}" height="16" fill="#657e8a"/>
<text x="16" y="235" font-size="13">Stopped · {target:.2f}</text>
<text x="16" y="266" font-size="14" font-weight="700">Best of 49 shuffled searches</text>
<rect x="32" y="278" width="{x(shuffled)-32:.1f}" height="16" fill="#a1b0b8"/>
<text x="16" y="314" font-size="13">Stopped · {shuffled:.2f}</text>
<text x="16" y="339" font-size="13" font-weight="700">No key fits were attempted on LP2.</text>
</g></svg>'''

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    target_file = H / "gate.svg"
    raw = make().encode("utf8")
    if args.check:
        assert target_file.read_bytes() == raw
    else:
        target_file.write_bytes(raw)
    print("source-gate visual", len(raw), "bytes")

if __name__ == "__main__":
    main()
