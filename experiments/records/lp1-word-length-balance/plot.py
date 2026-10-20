"""Create the word-length table and observed column-mean plot; no new tests."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text())
words = json.loads((HERE / "words.json").read_text(encoding="utf-8"))
with (HERE / "length-table.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["row"] + [f"column_{i}" for i in range(1, 17)])
    for i in range(29):
        writer.writerow([i + 1] + [w["rune_length"] for w in words[i * 16:(i + 1) * 16]])
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="360" height="330" viewBox="0 0 360 330" role="img" aria-labelledby="title desc">',
         '<title id="title">Mean rune-word length in each of sixteen columns</title>',
         '<desc id="desc">Every column has 29 words. Means range from 101/29 to 126/29 runes. The dashed line marks the overall mean, 1796/464. This plots the observation, not the shuffle distribution.</desc>',
         '<rect width="360" height="330" fill="#faf9f5"/>',
         '<g font-family="Arial,sans-serif" fill="#263b45">',
         '<text x="18" y="27" font-size="18">Sixteen column means</text>',
         '<text x="18" y="49" font-size="14">Runes per word · 29 words per column</text>']
for value in range(6):
    y = 250 - value * 32
    parts.append(f'<path d="M40 {y}H344" stroke="#d7dcde"/><text x="28" y="{y+5}" text-anchor="end" font-size="13">{value}</text>')
for i, total in enumerate(result["column_sums"]):
    height = total / 29 * 32
    x = 46 + i * 18
    parts.append(f'<rect x="{x}" y="{250-height:.3f}" width="12" height="{height:.3f}" fill="#365a6d"/>')
    if i in (0, 3, 7, 11, 15):
        parts.append(f'<text x="{x+6}" y="270" font-size="13" text-anchor="middle">{i+1}</text>')
y = 250 - result["runes"] / result["words"] * 32
parts += [f'<path d="M40 {y:.3f}H344" stroke="#9b4237" stroke-width="2" stroke-dasharray="4 3"/>',
          '<text x="180" y="291" text-anchor="middle" font-size="14">Column in the original word order</text>',
          '<text x="18" y="318" font-size="13">Dashed line: overall mean (3.871 runes)</text></g></svg>']
(HERE / "column-means.svg").write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
print("Saved 29 × 16 CSV and column-mean SVG")
