"""Draw the stored LP1-16 fixed-center counterexample as changes to the grid."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
e = next(e for e in r["counterexamples"] if e["page"] == "lp1-16" and e["fixed_cell_one_based"] == [3, 3])
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="350" viewBox="0 0 360 350" role="img" aria-labelledby="title desc">', '<title id="title">A change that preserves the 3301 square</title>', '<desc id="desc">Add one at row two column one and row four column five; subtract one at row two column five and row four column one. All other entries, including center 809, are unchanged.</desc>', '<rect width="360" height="350" fill="white"/>', '<g font-family="sans-serif" text-anchor="middle">', '<text x="180" y="25" font-size="16" fill="#25343b">Change four cells; keep every line sum</text>']
for row in range(5):
 for col in range(5):
  delta = e["positive_counterexample"][row][col] - e["original"][row][col]
  x, y = 55 + col*50, 45 + row*50
  fill = "#d8e8ed" if delta else "#f6f6f2"
  label = f"{delta:+d}" if delta else "0"
  if (row, col) == (2, 2): label = "809"
  svg += [f'<rect x="{x}" y="{y}" width="50" height="50" fill="{fill}" stroke="#79868b"/>', f'<text x="{x+25}" y="{y+31}" font-size="18" fill="#25343b">{label}</text>']
svg += ['<text x="180" y="320" font-size="13" fill="#43545b">0 = no change; center 809 stays fixed</text>', '<text x="180" y="340" font-size="13" fill="#43545b">Constructed example, not a manuscript image</text>', '</g></svg>']
(HERE / "fixed-center.svg").write_text("\n".join(svg)+"\n", encoding="utf-8", newline="\n")
