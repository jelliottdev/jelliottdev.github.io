"""Create a compact, source-bound view of each draft's actual coverage."""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def make() -> None:
    rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["variants"]
    counts = {row["source_file"]: row["positions_processed"] for row in rows}
    assert counts == {"OG_quag_mirror.py": 153, "quag_mirror_v4.py": 49,
                      "quag_mirror_WIP.py": 500}
    x0, x1 = 95, 363
    x = lambda value: x0 + value / 729 * (x1 - x0)
    bars = ""
    for y, title, name in ((92, "Original", "OG_quag_mirror.py"),
                           (137, "Version 4", "quag_mirror_v4.py"),
                           (182, "WIP", "quag_mirror_WIP.py")):
        value = counts[name]
        bars += (f'<text x="18" y="{y+5}" class="label">{title}</text>'
                 f'<rect x="{x0}" y="{y-10}" width="{x1-x0}" height="16" fill="#eef1f3"/>'
                 f'<rect x="{x0}" y="{y-10}" width="{x(value)-x0:.1f}" height="16" fill="#315f78"/>'
                 f'<text x="{min(x(value)+6,337):.1f}" y="{y+3}" class="value">{value}</text>')
    guides = "".join(
        f'<line x1="{x(value):.1f}" y1="77" x2="{x(value):.1f}" y2="195" stroke="#a6b1b7" stroke-dasharray="3 3"/>'
        f'<text x="{x(value):.1f}" y="68" text-anchor="middle" class="tick">{label}</text>'
        for value, label in ((262, "end 00"), (528, "end 01")))
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 390 230">
<title id="title">Three QuagMirror variants stop before completing their 729-rune source section</title>
<desc id="desc">Original stops after 153 runes, version 4 after 49, and WIP after 500. The fixed source section spans LP2 pages 00 through 02, with page boundaries after runes 262 and 528.</desc>
<rect width="390" height="230" fill="white"/>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#26343e}}.label{{font-size:13px;font-weight:600}}.value{{font-size:12px}}.tick{{font-size:10px}}</style>
<text x="18" y="29" font-size="18" font-weight="700">How far the drafts run</text>
<text x="18" y="48" font-size="12">Each begins at LP2-00; the source section has 729 runes.</text>
{bars}{guides}
<text x="18" y="217" font-size="11">Fixed debug stops; none reaches the end of LP2-02.</text>
</svg>'''
    (HERE / "coverage.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
