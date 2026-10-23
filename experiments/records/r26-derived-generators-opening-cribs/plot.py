"""Generate a small, legible SVG of the fixed-opening result."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OUT = HERE / "opening-prefixes.svg"


def make_svg():
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    hist = {int(k): v for k, v in data["best_prefix_histogram"].items()}
    assert sum(hist.values()) == data["actual_preset_rows"] == 48462
    assert not data["exact_matches"]
    most = max(hist)
    boxes = "".join(
        f'<rect x="{37+i*44}" y="81" width="36" height="36" rx="3" '
        f'fill="{("#315b72" if i < most else "#edf0f2")}" stroke="{("#315b72" if i < most else "#aab3b9")}"/>'
        for i in range(12)
    )
    chart = []
    maximum = max(hist.values())
    for row, length in enumerate((1, 2, 3, 4)):
        y = 170 + row * 34
        width = 320 * hist.get(length, 0) / maximum
        chart.append(f'<text x="40" y="{y+15}" class="label">{length} rune{"s" if length != 1 else ""}</text>'
                     f'<rect x="155" y="{y}" width="{width:.1f}" height="21" fill="#315b72"/>'
                     f'<text x="{max(165+width,175):.1f}" y="{y+16}" class="count">{hist.get(length,0):,}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360" role="img" aria-labelledby="title desc">
<title id="title">Longest familiar opening: four of twelve runes</title>
<desc id="desc">Among 48,462 source-defined generator and skip-model configurations, none matched a complete twelve-rune opening on any of 55 pages. The best matched four runes. Counts by longest prefix: one {hist.get(1,0)}, two {hist.get(2,0)}, three {hist.get(3,0)}, four {hist.get(4,0)}.</desc>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#26343d}} .title{{font-size:25px;font-weight:700}} .note{{font-size:16px;fill:#52636c}} .label{{font-size:17px}} .count{{font-size:17px;font-weight:700}}</style>
<rect width="600" height="360" fill="#f7f8f9"/>
<text x="38" y="42" class="title">The closest opening matched 4 of 12 runes</text>
<text x="38" y="65" class="note">No complete match in 48,462 tested configurations</text>
{boxes}
<text x="38" y="145" class="note">Longest feasible prefix per configuration</text>
{''.join(chart)}
<text x="38" y="334" class="note">Nine fixed openings · 55 page starts · two skip rules</text>
</svg>
'''
    return svg


def main():
    svg = make_svg()
    if "--check" in sys.argv:
        assert OUT.read_text(encoding="utf-8") == svg
        print("SVG matches results")
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
        print(OUT)


if __name__ == "__main__":
    main()
