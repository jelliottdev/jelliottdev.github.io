"""Draw the fixed-crib fit census in a phone-width SVG."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
colors = {"impossible": "#aab6bd", "unique": "#2d6782", "ambiguous": "#43545e"}
rows = []
for period in range(1, 9):
    summary = result["by_period"][str(period)]
    y = 103 + (period - 1) * 30
    x = 55.0
    segments = []
    for label in ("impossible", "unique", "ambiguous"):
        width = summary[label] * 185 / 495
        if width:
            segments.append(f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="16" fill="{colors[label]}"/>')
        x += width
    fits = summary["unique"] + summary["ambiguous"]
    rows.append(f'<text x="16" y="{y + 13}" font-family="Arial,sans-serif" font-size="14" fill="#25343c">p{period}</text>'
                + "".join(segments)
                + f'<text x="250" y="{y + 13}" font-family="Arial,sans-serif" font-size="13" fill="#25343c">{fits} fit</text>')
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 370" role="img" aria-labelledby="title desc">
<title id="title">Periodic affine fits to fixed openings</title>
<desc id="desc">Five short periods fit none of the 495 page and proposed-opening pairs. At period six, 287 fit, mostly with one compatible key. Periods seven and eight fit 262 and 293 pairs, all with multiple compatible keys.</desc>
<rect width="340" height="370" fill="#f4f5f6"/>
<text x="16" y="26" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#20282e">When can the openings fit?</text>
<text x="16" y="46" font-family="Arial,sans-serif" font-size="13" fill="#4c5960">495 page + crib pairs at each period</text>
<rect x="16" y="62" width="11" height="11" fill="#aab6bd"/><text x="31" y="72" font-family="Arial,sans-serif" font-size="13" fill="#35444d">No key</text>
<rect x="98" y="62" width="11" height="11" fill="#2d6782"/><text x="113" y="72" font-family="Arial,sans-serif" font-size="13" fill="#35444d">One key</text>
<rect x="183" y="62" width="11" height="11" fill="#43545e"/><text x="198" y="72" font-family="Arial,sans-serif" font-size="13" fill="#35444d">Many keys</text>
''' + "\n".join(rows) + '''
<text x="16" y="360" font-family="Arial,sans-serif" font-size="13" fill="#4c5960">A fit is conditional on a proposed opening.</text>
</svg>
'''
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
path = HERE / "fits.svg"
if args.check:
    assert svg == path.read_text(encoding="utf-8")
    print("SVG matches saved counts")
else:
    path.write_text(svg, encoding="utf-8", newline="\n")
