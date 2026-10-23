"""Render a small responsive comparison using fixed experiment results."""
import html
import json
from pathlib import Path

here = Path(__file__).resolve().parent
r = json.loads((here / "results.json").read_text(encoding="utf-8"))
scores = [r["direct_hits"], r["best_rail_hits"], sorted(r["control_best_hits"])[len(r["control_best_hits"]) // 2]]
labels = ["Unchanged text", "Best of 9 rail counts", "Control median"]
colors = ["#8e979d", "#2d5a70", "#596d78"]
rows = []
for i, (label, value, color) in enumerate(zip(labels, scores, colors)):
    y = 64 + i * 54
    width = round(value * 2.9, 1)
    rows.append(f'<text x="16" y="{y}" font-size="14">{html.escape(label)}</text><rect x="16" y="{y+11}" width="{width}" height="16" fill="{color}"/><text x="{round(22+width,1)}" y="{y+25}" font-size="13">{value}</text>')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 245" role="img" aria-labelledby="title desc"><title id="title">Rail fence word matches</title><desc id="desc">Unchanged text has {scores[0]} hits; the best rail setting has {scores[1]}; the median control has {scores[2]}.</desc><rect width="360" height="245" fill="#f4f6f7"/><g fill="#20323b" font-family="system-ui, sans-serif"><text x="16" y="30" font-size="17" font-weight="700">Matched words across LP2-00–55</text>{''.join(rows)}<text x="16" y="228" font-size="12">Same 369,652-word list · 2,776 visible word slots</text></g></svg>'''
(here / "comparison.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
