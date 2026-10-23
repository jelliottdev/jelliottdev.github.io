"""Create a small, scalable comparison of the two declared null models."""
from __future__ import annotations

import json
from pathlib import Path
import xml.sax.saxutils as sx

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
obs = d["line_initial"]["chi2"]
layout = d["line_initial"]["layout_mean"]
flat = 26.9  # original source's 200,000-draw flat-null mean, rounded as published
scale = 4.85


def bar(y: int, value: float, color: str, label: str, sub: str) -> str:
    return (f'<text x="22" y="{y-13}" class="label">{sx.escape(label)}</text>'
            f'<rect x="22" y="{y}" width="{value*scale:.1f}" height="28" fill="{color}"/>'
            f'<text x="{32+value*scale:.1f}" y="{y+20}" class="value">{value:.1f}</text>'
            f'<text x="22" y="{y+48}" class="note">{sx.escape(sub)}</text>')


svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 395" role="img"
 aria-labelledby="title desc" style="max-width:100%;height:auto">
<title id="title">Why the first rune of each line looked unusual</title>
<desc id="desc">The observed chi-square is 78.7. A flat shuffle expects 26.9, but a layout-aware shuffle expects 66.5. The observed value is ordinary under layout, p 0.195.</desc>
<style>.title{{font:600 20px system-ui,sans-serif;fill:#20272b}}.label{{font:600 16px system-ui,sans-serif;fill:#20272b}}.value{{font:600 15px system-ui,sans-serif;fill:#20272b}}.note{{font:14px system-ui,sans-serif;fill:#526068}}.footer{{font:14px system-ui,sans-serif;fill:#334249}}</style>
<rect width="620" height="395" fill="#f7f8f9"/>
<text x="22" y="35" class="title">First runes of physical lines</text>
<text x="22" y="60" class="note">Departure from the manuscript’s overall rune frequencies (χ²)</text>
{bar(103,flat,'#91a2ad','Flat shuffle','Ignores why line breaks fall where they do')}
{bar(195,layout,'#516f80','Reflowed shuffle','Shuffles runes, then breaks lines by fitted glyph widths')}
{bar(287,obs,'#244c63','Manuscript','Unusual against flat shuffle; ordinary after reflow')}
<line x1="22" y1="358" x2="598" y2="358" stroke="#c4ccd1"/>
<text x="22" y="382" class="footer">Layout-aware p = {d['line_initial']['p_layout']:.3f} · 2,000 reflows · 594 line starts</text>
</svg>'''
(HERE / "layout-control.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")
print("layout-control.svg")

power = json.loads((HERE / "replay-power.json").read_text(encoding="utf-8"))
curves = {
    name: sorted((row for row in power["curve"] if row["mechanism"] == name),
                 key=lambda row: row["f"])
    for name in ("M1_assign", "M2_filter_wins")
}

def coords(rows: list[dict]) -> str:
    return " ".join(f"{70 + row['f'] * 490:.1f},{294 - row['power_D_layout'] * 210:.1f}"
                    for row in rows)

power_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 370" role="img"
 aria-labelledby="power-title power-desc" style="max-width:100%;height:auto">
<title id="power-title">How much planted line-initial forcing the corrected test detects</title>
<desc id="power-desc">Two planted mechanisms have zero of two hundred detections at zero forcing, about half at forty percent, and all trials detected at sixty percent or more.</desc>
<style>.title{{font:600 19px system-ui,sans-serif;fill:#20272b}}.axis{{font:14px system-ui,sans-serif;fill:#46545c}}.label{{font:600 14px system-ui,sans-serif;fill:#20272b}}.note{{font:13px system-ui,sans-serif;fill:#59666d}}</style>
<rect width="620" height="370" fill="#f7f8f9"/>
<text x="22" y="34" class="title">Planted line-initial signal: detection rate</text>
<text x="22" y="57" class="note">Layout-corrected test · 200 synthetic trials per setting</text>
<line x1="70" y1="84" x2="70" y2="294" stroke="#a9b5bb"/>
<line x1="70" y1="294" x2="560" y2="294" stroke="#a9b5bb"/>
<line x1="70" y1="126" x2="560" y2="126" stroke="#d1d9dd" stroke-dasharray="5 5"/>
<text x="28" y="90" class="axis">100%</text><text x="34" y="132" class="axis">80%</text>
<text x="41" y="299" class="axis">0%</text>
<text x="66" y="318" class="axis">0</text><text x="257" y="318" class="axis">40%</text>
<text x="355" y="318" class="axis">60%</text><text x="536" y="318" class="axis">100%</text>
<polyline points="{coords(curves['M1_assign'])}" fill="none" stroke="#244c63" stroke-width="3"/>
<polyline points="{coords(curves['M2_filter_wins'])}" fill="none" stroke="#718d9b" stroke-width="3" stroke-dasharray="7 5"/>
<circle cx="364" cy="84" r="4" fill="#244c63"/>
<text x="410" y="105" class="label">Both reach 100% at 60%</text>
<text x="70" y="352" class="note">Solid: write chosen rune · Dashed: anti-repeat rule can override it</text>
</svg>'''
(HERE / "power-curve.svg").write_text(power_svg + "\n", encoding="utf-8", newline="\n")
print("power-curve.svg")
