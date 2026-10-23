"""Small-screen score plot for the fixed B04 source stages."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
items = [
    ("Planted control", r["g2"]["source_plant_score_direct"], True),
    ("A · 120 runes", r["stage_best"]["A"], False),
    ("B · 120 runes", r["stage_best"]["B"], False),
    ("C · page starts", r["stage_best"]["C"], False),
    ("D · full page", r["stage_best"]["D"]["D_page0_full"], False),
    ("D · all runes", r["stage_best"]["D"]["D_unsolved_full"], False),
]


def x(score):
    return 153 + (score + 8) * 32.5


lines = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 356" role="img" aria-labelledby="title desc">',
    '<title id="title">B04 planted control and LP2 scores</title>',
    '<desc id="desc">The planted control exceeds the source advancement bar of minus 5.5. None of the five LP2 stage best scores do.</desc>',
    '<rect width="360" height="356" fill="#f7f9fb"/>',
    '<text x="16" y="26" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#243543">Source score screen</text>',
    '<text x="16" y="46" font-family="Arial,sans-serif" font-size="13" fill="#50616c">Higher is more English-like in this model</text>',
    f'<line x1="{x(-5.5):.1f}" y1="76" x2="{x(-5.5):.1f}" y2="305" stroke="#78909e" stroke-width="1.5" stroke-dasharray="5 4"/>',
    f'<text x="{x(-5.5)+5:.1f}" y="70" font-family="Arial,sans-serif" font-size="13" fill="#50616c">bar −5.5</text>',
]
for i, (name, score, plant) in enumerate(items):
    y = 99 + i * 40
    color = "#1f766e" if plant else "#2e5571"
    lines.extend([
        f'<text x="16" y="{y+5}" font-family="Arial,sans-serif" font-size="13" fill="#243543">{escape(name)}</text>',
        f'<line x1="153" y1="{y}" x2="{x(score):.1f}" y2="{y}" stroke="{color}" stroke-width="3"/>',
        f'<circle cx="{x(score):.1f}" cy="{y}" r="5" fill="{color}"/>',
        f'<text x="290" y="{y+5}" font-family="Arial,sans-serif" font-size="13" fill="#243543">{score:.3f}</text>',
    ])
lines += [
    '<line x1="153" y1="325" x2="283" y2="325" stroke="#78909e"/>',
    '<text x="147" y="345" font-family="Arial,sans-serif" font-size="13" fill="#50616c">−8</text>',
    '<text x="267" y="345" font-family="Arial,sans-serif" font-size="13" fill="#50616c">−4</text>',
    '</svg>',
]
(HERE / "scores.svg").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
