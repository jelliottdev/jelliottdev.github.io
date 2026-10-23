"""Render the two model comparisons as a compact phone-readable SVG."""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
path = HERE / "replay-source.json"
if not path.exists():
    path = HERE / "source" / "original_results.json"
d = json.loads(path.read_text(encoding="utf-8"))


def dot(y: int, label: str, value: float, scale: str,
        sd: float | None = None, actual: bool = False) -> str:
    if scale == "balance":
        x = 145 + (value - .60) / .42 * 245
        delta = (sd or 0) / .42 * 245
    else:
        x = 145 + value / .30 * 245
        delta = (sd or 0) / .30 * 245
    color = "#244c63" if actual else "#6d8795"
    whisker = (f'<line x1="{x-delta:.1f}" x2="{x+delta:.1f}" y1="{y}" y2="{y}" '
               f'stroke="{color}" stroke-width="3"/>') if sd is not None else ""
    return (f'<text x="16" y="{y+5}" class="row">{escape(label)}</text>'
            f'{whisker}<circle cx="{x:.1f}" cy="{y}" r="{5 if actual else 4}" fill="{color}"/>')


w = d["real"]["chi2W58_mean"]
cross = d["real"]["dbl_line_cross_rate"]
controls = d["controls"]
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 444" role="img"
 aria-labelledby="title desc" style="max-width:100%;height:auto">
<title id="title">Which matched filter model resembles the manuscript</title>
<desc id="desc">LP2's 58-rune window balance is close to a lag-one-only filter but above tested recency-avoidance controls. Four of 86 doublets cross a line, close to the continuous-filter control and far below a line-reset control.</desc>
<style>.title{{font:600 18px system-ui,sans-serif;fill:#20272b}}.head{{font:600 15px system-ui,sans-serif;fill:#263239}}.row{{font:14px system-ui,sans-serif;fill:#263239}}.tick{{font:12px system-ui,sans-serif;fill:#526068}}.note{{font:12px system-ui,sans-serif;fill:#526068}}</style>
<rect width="420" height="444" fill="#f7f8f9"/>
<text x="16" y="30" class="title">Matched controls, not a raw repeat count</text>
<text x="16" y="62" class="head">Balance in 58-rune windows</text>
<text x="16" y="81" class="note">Higher = less short-window rebalancing · dots are means</text>
<line x1="145" x2="390" y1="110" y2="110" stroke="#aebbc2"/>
<text x="138" y="103" class="tick">0.60</text><text x="257" y="103" class="tick">0.80</text><text x="365" y="103" class="tick">1.00</text>
{dot(136,'LP2',w,'balance',actual=True)}
{dot(169,'Lag-one filter',controls['machine']['chi2W58_mean'][0],'balance',controls['machine']['chi2W58_mean'][1])}
{dot(202,'Weak recency',controls['hand_bleed_tiny']['chi2W58_mean'][0],'balance',controls['hand_bleed_tiny']['chi2W58_mean'][1])}
{dot(235,'More recency',controls['hand_bleed_small']['chi2W58_mean'][0],'balance',controls['hand_bleed_small']['chi2W58_mean'][1])}
<line x1="16" x2="404" y1="264" y2="264" stroke="#cbd4d9"/>
<text x="16" y="291" class="head">Share of doublets across a line</text>
<text x="16" y="309" class="note">A line-reset rule predicts many more boundary repeats</text>
<line x1="145" x2="390" y1="334" y2="334" stroke="#aebbc2"/>
<text x="140" y="328" class="tick">0%</text><text x="261" y="328" class="tick">15%</text><text x="365" y="328" class="tick">30%</text>
{dot(355,'LP2 · 4/86',cross,'cross',actual=True)}
{dot(386,'Continuous',controls['machine']['dbl_line_cross_rate'][0],'cross',controls['machine']['dbl_line_cross_rate'][1])}
{dot(410,'Line reset',controls['machine_lines']['dbl_line_cross_rate'][0],'cross',controls['machine_lines']['dbl_line_cross_rate'][1])}
<text x="16" y="438" class="note">Control whiskers show ±1 simulated standard deviation.</text>
</svg>'''
(HERE / "filter-models.svg").write_text(svg+"\n", encoding="utf-8", newline="\n")
print("filter-models.svg")
