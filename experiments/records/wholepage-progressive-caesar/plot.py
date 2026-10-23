"""Draw the observed maximum against full-search controls at phone width."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
values = sorted(result["null_maxima"])
q05 = values[round(.05 * (len(values) - 1))]
q95 = values[round(.95 * (len(values) - 1))]
middle = values[len(values) // 2]
weakest = min(row["source_score"] for row in result["control_gate"]["rows"])
best = result["best_case"]["score"]
scale = lambda n: round(70 + (n + 6.8) / 2.2 * 250, 1)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 260" role="img" aria-labelledby="title desc">
<title id="title">Progressive-shift English scores</title>
<desc id="desc">The best of 44,660 progressive-shift outputs scored minus 6.43, amid the full-search shuffle maxima. The weakest of nine complete known readings scored minus 4.98. Higher scores are more English-like.</desc>
<rect width="340" height="260" fill="#f4f5f6"/>
<text x="16" y="26" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#20282e">Progressive-shift scores</text>
<text x="16" y="47" font-family="Arial,sans-serif" font-size="13" fill="#4c5960">Higher is more like known readings →</text>
<line x1="70" x2="320" y1="213" y2="213" stroke="#617079" stroke-width="1.5"/>
<line x1="{scale(-6.5)}" x2="{scale(-6.5)}" y1="209" y2="217" stroke="#617079"/>
<line x1="{scale(-6)}" x2="{scale(-6)}" y1="209" y2="217" stroke="#617079"/>
<line x1="{scale(-5)}" x2="{scale(-5)}" y1="209" y2="217" stroke="#617079"/>
<text x="{scale(-6.5)}" y="237" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#35444d">−6.5</text>
<text x="{scale(-6)}" y="237" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#35444d">−6</text>
<text x="{scale(-5)}" y="237" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#35444d">−5</text>
<text x="16" y="86" font-family="Arial,sans-serif" font-size="13" fill="#35444d">Shuffles</text>
<line x1="{scale(q05)}" x2="{scale(q95)}" y1="100" y2="100" stroke="#9ca9b0" stroke-width="12" stroke-linecap="round"/>
<circle cx="{scale(middle)}" cy="100" r="6" fill="#415660"/>
<text x="16" y="130" font-family="Arial,sans-serif" font-size="13" fill="#35444d">LP2 best</text>
<circle cx="{scale(best)}" cy="143" r="7" fill="#285b75"/>
<text x="{scale(best) + 13}" y="148" font-family="Arial,sans-serif" font-size="13" fill="#285b75">−6.43</text>
<text x="16" y="174" font-family="Arial,sans-serif" font-size="13" fill="#35444d">Weakest known</text>
<circle cx="{scale(weakest)}" cy="187" r="7" fill="#34454d"/>
<text x="{scale(weakest) - 11}" y="193" text-anchor="end" font-family="Arial,sans-serif" font-size="13" fill="#34454d">−4.98</text>
</svg>
'''
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
path = HERE / "scores.svg"
if args.check:
    assert svg == path.read_text(encoding="utf-8")
    print("SVG matches saved scores")
else:
    path.write_text(svg, encoding="utf-8", newline="\n")
