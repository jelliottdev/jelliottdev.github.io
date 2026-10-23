"""Make a compact score comparison for the KDF source replay."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KDF = HERE / "source/liber-primus/analysis/round15/KDF"


def make() -> None:
    a = json.loads((KDF / "original_results_A.json").read_text(encoding="utf-8"))
    gates = json.loads((KDF / "original_results_gates.json").read_text(encoding="utf-8"))
    best = a["best_score"]
    planted = gates["K2"]["rank1"]["score"]
    bar = a["bar"]
    # A narrow canvas keeps labels readable when the figure fills a phone.
    left, right = 36, 344
    x = lambda s: left + (s + 7.5) / 4 * (right - left)
    ticks = "".join(f'<line x1="{x(v):.1f}" y1="78" x2="{x(v):.1f}" y2="250" stroke="#e3e9ed"/>'
                    f'<text x="{x(v):.1f}" y="270" text-anchor="middle" class="small">{v:.0f}</text>'
                    for v in (-7, -6, -5, -4))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 380 306">
<title id="title">KDF source replay: planted control versus best LP2 result</title>
<desc id="desc">The planted control scores {planted:.3f} and clears the minus 5.5 bar. The best LP2 decoding scores {best:.3f} and does not.</desc>
<rect width="380" height="306" fill="white"/>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#25333e}}.small{{font-size:13px}}.label{{font-size:16px}}.value{{font-size:16px;font-weight:bold}}</style>
<text x="24" y="32" font-size="20" font-weight="700">Key-stretching screen</text>
<text x="24" y="56" class="small">English score · higher is stronger</text>
{ticks}
<line x1="{x(bar):.1f}" y1="78" x2="{x(bar):.1f}" y2="250" stroke="#667985" stroke-width="2" stroke-dasharray="5 4"/>
<text x="{x(bar)+6:.1f}" y="91" class="small">bar −5.5</text>
<text x="36" y="122" class="label">Planted control</text>
<text x="344" y="122" text-anchor="end" class="value">{planted:.3f}</text>
<line x1="{left}" y1="145" x2="{x(planted):.1f}" y2="145" stroke="#315f78" stroke-width="12"/>
<circle cx="{x(planted):.1f}" cy="145" r="7" fill="#315f78"/>
<text x="36" y="197" class="label">Best LP2 candidate</text>
<text x="344" y="197" text-anchor="end" class="value">{best:.3f}</text>
<line x1="{left}" y1="220" x2="{x(best):.1f}" y2="220" stroke="#607c8c" stroke-width="12"/>
<circle cx="{x(best):.1f}" cy="220" r="7" fill="#607c8c"/>
<text x="24" y="297" class="small">The planted message passes; no LP2 candidate does.</text>
</svg>'''
    (HERE / "scores.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
