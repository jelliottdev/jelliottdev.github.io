"""Build a compact SVG showing the longest fixed opening for each L3 case."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OUT = HERE / "prior-front-prefixes.svg"


def make_svg():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    counts = {int(k): v for k, v in r["best_prefix_histogram"].items()}
    longest = max(counts)
    assert sum(counts.values()) == r["rows"] == 183900
    cells = "".join(f'<rect x="{36+i*43}" y="80" width="35" height="35" rx="3" '
                    f'fill="{("#315b72" if i < longest else "#edf0f2")}" '
                    f'stroke="{("#315b72" if i < longest else "#9ba9b2")}"/>'
                    for i in range(12))
    rows = []
    maximum = max(counts.values())
    for i, length in enumerate(sorted(counts)):
        y = 159 + i * 31
        width = 305 * counts[length] / maximum
        rows.append(f'<text x="38" y="{y+16}" class="label">{length} rune{"s" if length != 1 else ""}</text>'
                    f'<rect x="145" y="{y}" width="{width:.1f}" height="20" fill="#315b72"/>'
                    f'<text x="{155+width:.1f}" y="{y+16}" class="number">{counts[length]:,}</text>')
    height = 205 + len(rows) * 31
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 {height}" role="img" aria-labelledby="title desc">
<title id="title">Closest Python 2.7 seed opening: {longest} of 12 runes</title>
<desc id="desc">Across {r['rows']:,} reducer and seed cases, zero match all twelve fixed opening runes. The best match is {longest}. Counts by longest prefix: {', '.join(f'{k} runes {v}' for k,v in sorted(counts.items()))}.</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#26343d}} .title{{font-size:25px;font-weight:700}} .note{{font-size:16px;fill:#52636c}} .label{{font-size:17px}} .number{{font-size:17px;font-weight:700}}</style>
<rect width="600" height="{height}" fill="#f7f8f9"/>
<text x="36" y="42" class="title">The closest opening matched {longest} of 12 runes</text>
<text x="36" y="65" class="note">{r['rows']:,} generated cases · zero complete openings</text>
{cells}
<text x="36" y="141" class="note">Longest feasible prefix per generated case</text>
{''.join(rows)}
<text x="36" y="{height-16}" class="note">Four source settings · 45,975 priority words · 55 pages</text>
</svg>
'''


if __name__ == "__main__":
    svg = make_svg()
    if "--check" in sys.argv:
        assert OUT.read_text(encoding="utf-8") == svg
        print("SVG matches results")
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
        print(OUT)
