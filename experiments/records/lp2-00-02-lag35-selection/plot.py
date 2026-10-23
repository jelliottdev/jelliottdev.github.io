"""Render the full-scan null distribution as a compact responsive SVG."""
import json
from pathlib import Path

here = Path(__file__).resolve().parent
r = json.loads((here / "results.json").read_text(encoding="utf-8"))
maxima = r["control_max_z"]
edges = [2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5]
bars = [sum(a <= z < b for z in maxima) for a, b in zip(edges, edges[1:])]
widths = [round(230 * n / max(bars), 1) for n in bars]
rows = []
for i, (left, right, count, width) in enumerate(zip(edges, edges[1:], bars, widths)):
    y = 60 + i * 29
    color = "#2d5a70" if left <= r["observed_best_z"] < right else "#82969f"
    rows.append(f'<text x="14" y="{y+13}" font-size="12">{left:.1f}–{right:.1f}</text><rect x="78" y="{y}" width="{width}" height="18" fill="{color}"/><text x="{84+width}" y="{y+14}" font-size="12">{count}</text>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 295" role="img" aria-labelledby="title desc"><title id="title">Strongest lag in each control</title><desc id="desc">The observed strongest z score is 3.76. Eighty-two of 999 controls reach it after selecting from 242 lags.</desc><rect width="360" height="295" fill="#f4f6f7"/><g fill="#22343d" font-family="system-ui, sans-serif"><text x="14" y="28" font-size="17" font-weight="700">Strongest lag in each control</text>{''.join(rows)}<text x="14" y="275" font-size="12">Observed: z = 3.76 · 82/999 controls ≥ it</text></g></svg>'''
(here / "selection.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
