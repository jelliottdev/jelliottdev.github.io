"""Render source-measured scorer comparison as a phone-readable SVG."""
import json
from html import escape
from pathlib import Path

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/"results.json").read_text(encoding="utf-8"))
pages=r["solved_pages"]
left,right=215,550
scale=(right-left)/2.0  # score range -5.5 to -3.5
pos=lambda score:left+(score+5.5)*scale
out=[
'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 520" role="img" aria-labelledby="title desc">',
'<title id="title">Rune-matched scorer helps solved-page scores but does not tighten wrong-key noise</title>',
'<desc id="desc">All five solved pages score somewhat higher under the transformed quadgram model. Wrong-key noise standard deviation rises from 0.0880 to 0.0895, so the promised noise tightening is not reproduced.</desc>',
'<style>text{font-family:Arial,Helvetica,sans-serif;fill:#23343d}.title{font-size:22px;font-weight:700}.sub{font-size:16px;fill:#536671}.label{font-size:17px}.key{font-size:15px}.old{fill:#8b9ca4}.new{fill:#2d6078}.rule{stroke:#cbd3d7;stroke-width:1}.pair{stroke:#9aabb3;stroke-width:2}</style>',
'<rect width="600" height="520" fill="#fff"/>',
'<text x="20" y="35" class="title">Solved-page scores</text>',
'<text x="20" y="62" class="sub">Higher is better. Both models use the same decoded text.</text>',
'<circle cx="30" cy="90" r="6" class="old"/><text x="45" y="95" class="key">Original quadgrams</text>',
'<circle cx="250" cy="90" r="6" class="new"/><text x="265" y="95" class="key">Alias-collapsed quadgrams</text>',
]
for i,p in enumerate(pages):
    y=137+i*50
    x1,x2=pos(p["old_score"]),pos(p["new_score"])
    out.extend([f'<text x="20" y="{y+6}" class="label">{escape(p["page"].title())}</text>',
                f'<line x1="{x1:.1f}" x2="{x2:.1f}" y1="{y}" y2="{y}" class="pair"/>',
                f'<circle cx="{x1:.1f}" cy="{y}" r="6" class="old"/>',
                f'<circle cx="{x2:.1f}" cy="{y}" r="7" class="new"/>'])
out += [
'<line x1="215" x2="550" y1="389" y2="389" class="rule"/>',
'<text x="215" y="413" class="sub">−5.5</text><text x="508" y="413" class="sub">−3.5</text>',
'<line x1="20" x2="580" y1="436" y2="436" class="rule"/>',
'<text x="20" y="468" class="label">Wrong-key score spread</text>',
f'<text x="20" y="499" class="sub">Original SD {r["null"]["old"]["sd"]:.4f}  →  transformed SD {r["null"]["new"]["sd"]:.4f}; it widened slightly.</text>',
'</svg>'
]
(HERE/"scorer-comparison.svg").write_text("\n".join(out)+"\n",encoding="utf-8",newline="\n")
