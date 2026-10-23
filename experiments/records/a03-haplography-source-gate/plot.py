"""Create a compact mobile-legible gate diagram from the checked result."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text())
assert r["agreement_gate_passed"] is False
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 330" role="img" aria-labelledby="t d">
<title id="t">The A-03 count audit does not establish its proposed limit</title>
<desc id="d">The image agreement is {r['agreement_percent']:.3f} percent, below the declared 99.5 percent gate. Twenty-six is an observed difference, not a bound on hidden merges; the proposed autokey threshold is ninety-three.</desc>
<rect width="340" height="330" fill="#f5f7f8"/>
<text x="16" y="30" fill="#202a31" font-family="Arial,sans-serif" font-size="19" font-weight="700">Two checks on the source claim</text>
<text x="16" y="65" fill="#273c48" font-family="Arial,sans-serif" font-size="15" font-weight="700">Image-reader gate</text>
<text x="16" y="92" fill="#202a31" font-family="Arial,sans-serif" font-size="16">Observed: {r['agreement_percent']:.3f}%</text>
<text x="16" y="118" fill="#202a31" font-family="Arial,sans-serif" font-size="16">Required: 99.5%</text>
<text x="16" y="169" fill="#8b3232" font-family="Arial,sans-serif" font-size="15" font-weight="700">Gate not met</text>
<line x1="16" y1="189" x2="324" y2="189" stroke="#c7d0d5"/>
<text x="16" y="218" fill="#273c48" font-family="Arial,sans-serif" font-size="15" font-weight="700">Doublet counts</text>
<text x="16" y="246" fill="#202a31" font-family="Arial,sans-serif" font-size="16">26 observed excess pairs</text>
<text x="16" y="271" fill="#202a31" font-family="Arial,sans-serif" font-size="16">93 proposed restoration threshold</text>
<text x="16" y="303" fill="#465962" font-family="Arial,sans-serif" font-size="14">An excess count is not an error bound.</text>
</svg>
'''
out = HERE / "gate-audit.svg"
out.write_text(svg, encoding="utf-8")
print(out)
