"""Render the complete pair matrix as a deterministic, accessible SVG."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
ids = list(r["row_bands"])
lookup = {(p["left"], p["right"]): p for p in r["pairs"]}
svg = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="760" height="610" viewBox="0 0 760 610" role="img" aria-labelledby="title desc">',
    '<title id="title">Text-row alignment of LP2-40 through LP2-48</title>',
    '<desc id="desc">All 36 pair comparisons under one fixed image crop. Blue outlines indicate adjacent pairs; gray cells are nonadjacent controls. Several nonadjacent pairs match as completely as adjacent pairs.</desc>',
    '<rect width="760" height="610" fill="#fff"/>',
    '<text x="36" y="40" font-family="Georgia,serif" font-size="24" fill="#1c2b33">Do neighboring pages align uniquely?</text>',
    '<text x="36" y="70" font-family="Arial,sans-serif" font-size="14" fill="#536168">LP2-40–48 · fixed crop · no vertical shift · row-mask Jaccard</text>',
]
for i, a in enumerate(ids):
    svg.append(f'<text x="{224+i*56}" y="106" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#33454f">{a[-2:]}</text>')
    svg.append(f'<text x="166" y="{145+i*49}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#33454f">{a}</text>')
    for j, b in enumerate(ids):
        x, y = 196+j*56, 114+i*49
        if i >= j:
            svg.append(f'<rect x="{x}" y="{y}" width="54" height="47" fill="#f3f4f2"/>')
            continue
        p = lookup[(a,b)]
        score = p["jaccard"]
        tone = round(246-118*score)
        color = f'rgb({tone},{tone+12},{tone+16})'
        border = '#225c79' if p["adjacent"] else '#d0d5d5'
        svg.append(f'<rect x="{x}" y="{y}" width="54" height="47" fill="{color}" stroke="{border}" stroke-width="{3 if p["adjacent"] else 1}"/>')
        svg.append(f'<text x="{x+27}" y="{y+29}" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#14232c">{score:.2f}</text>')
svg.extend([
    '<rect x="202" y="566" width="20" height="18" fill="#d4dfe3" stroke="#225c79" stroke-width="3"/>',
    '<text x="234" y="580" font-family="Arial,sans-serif" font-size="13" fill="#33454f">Adjacent</text>',
    '<rect x="340" y="566" width="20" height="18" fill="#d4dfe3" stroke="#d0d5d5"/>',
    '<text x="372" y="580" font-family="Arial,sans-serif" font-size="13" fill="#33454f">Nonadjacent control</text>',
    '</svg>',
])
(HERE / "row-alignment.svg").write_text("\n".join(svg)+"\n", encoding="utf-8")
print("row-alignment.svg written")
