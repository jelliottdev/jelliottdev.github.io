"""Two mobile-readable pictures of event placement and line-break rates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def placement() -> str:
    inp = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
    sizes = inp["source_segment_lengths"]
    events = {i: [] for i in range(7, 16)}
    for r in inp["pairs"]:
        if r[3] == r[4]:
            events[r[0]].append(r[1])
    assert sum(map(len, events.values())) == 86
    names = ("Crosses", "Sprouts", "Roots", "Square", "Möbius", "Dots", "Wing", "Cuneiform", "Plants")
    rows = []
    for j, size in enumerate(sizes):
        seg, y = j + 7, 111 + 31 * j
        width = max(2, 150 * size / max(sizes))
        ticks = "".join(f'<line x1="{110 + width*i/max(1,size-1):.2f}" y1="{y-6}" x2="{110 + width*i/max(1,size-1):.2f}" y2="{y+6}" stroke="#155b78" stroke-width="2"/>' for i in events[seg])
        rows.append(f'<text x="16" y="{y+5}" class="label">{names[j]}</text><rect x="110" y="{y-5}" width="{width:.2f}" height="10" fill="#e5eaee"/>{ticks}<text x="301" y="{y+5}" text-anchor="end" class="label">{len(events[seg])}</text>')
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 430" role="img" aria-labelledby="title desc">
<title id="title">Where the 86 adjacent repeats occur</title>
<desc id="desc">Nine source manuscript sections are bars proportional to rune lengths. Each blue mark is one surviving adjacent equal-rune pair; longer sections contain more events. The nine-rune section has none.</desc>
<style>text{font-family:Arial,Helvetica,sans-serif;fill:#25313a}.title{font-size:16px;font-weight:700}.note{font-size:14px;fill:#53616b}.label{font-size:14px}</style>
<rect x="1" y="1" width="318" height="428" fill="#fff" stroke="#ccd3d7"/>
<text x="16" y="29" class="title">Where do repeats survive?</text>
<text x="16" y="53" class="note">Each blue mark is one equal-rune pair.</text>
<text x="16" y="74" class="note">Bar length shows section length.</text>
<text x="16" y="95" class="note">Section feature</text><text x="301" y="95" class="note" text-anchor="end">Pairs</text>
''' + "\n".join(rows) + '''
<line x1="16" y1="390" x2="304" y2="390" stroke="#ccd3d7"/>
<text x="16" y="411" class="note">86 across 12,947 possible pairs</text>
</svg>'''


def boundaries() -> str:
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    a, n = d["H_L2"]["break_counts"]["within-line"]
    b, m = d["H_L2"]["break_counts"]["line-break"]
    assert (a, n, b, m) == (82, 12362, 4, 585)
    first, second = 196 * (a/n) / .025, 196 * (b/m) / .025
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 244" role="img" aria-labelledby="title desc">
<title id="title">Line ends have about the same repeat rate</title>
<desc id="desc">Within lines, 82 of 12,362 adjacent pairs repeat, about 0.66 percent. Across line breaks, 4 of 585 repeat, about 0.68 percent. The proposed line-end rule requires 2.5 percent.</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#25313a}}.title{{font-size:16px;font-weight:700}}.label{{font-size:14px}}.note{{font-size:14px;fill:#53616b}}</style>
<rect x="1" y="1" width="318" height="242" fill="#fff" stroke="#ccd3d7"/>
<text x="16" y="29" class="title">Do line ends act differently?</text>
<text x="16" y="56" class="label">Within written lines · 82 / 12,362</text>
<rect x="16" y="68" width="{first:.2f}" height="15" fill="#155b78"/>
<text x="16" y="103" class="label">Across line breaks · 4 / 585</text>
<rect x="16" y="115" width="{second:.2f}" height="15" fill="#155b78"/>
<line x1="212" y1="62" x2="212" y2="138" stroke="#73818a" stroke-width="2" stroke-dasharray="4 3"/>
<text x="16" y="161" class="note">Both rates are about 0.7%.</text>
<text x="16" y="183" class="note">Dashed line: proposed 2.5% rule.</text>
<line x1="16" y1="198" x2="304" y2="198" stroke="#ccd3d7"/>
<text x="16" y="222" class="note">No line-end increase appears here.</text>
</svg>'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    for name, svg in (("distribution.svg", placement()), ("line-breaks.svg", boundaries())):
        path = HERE / name
        if args.check:
            assert path.read_text(encoding="utf-8") == svg
        else:
            path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
