"""Draw the exact-channel planted skip count beside the 1% null-tail bar."""

from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = HERE / "source/liber-primus/analysis/round21/L2-nskips-crossover-length/original_nskips_crossover.json"


def make() -> None:
    data = json.loads(RESULT.read_text(encoding="utf-8"))
    rows = sorted((row for row in data["points"] if row["mode"] == "keyskip1"
                   and row["mech"] == "keyskip" and row["register"] == "LP1_REAL"),
                  key=lambda row: row["L"])
    assert len(rows) == 10
    left, right, top, bottom = 45, 357, 88, 280
    x = lambda length: left + (math.log(length) - math.log(400)) / (
        math.log(12956) - math.log(400)) * (right - left)
    y = lambda count: bottom - count / 450 * (bottom - top)
    poly = lambda key: " ".join(f"{x(row['L']):.1f},{y(row[key]):.1f}" for row in rows)
    grid = "".join(
        f'<line x1="{left}" y1="{y(v):.1f}" x2="{right}" y2="{y(v):.1f}" stroke="#e4e9ec"/>'
        f'<text x="38" y="{y(v)+4:.1f}" text-anchor="end" class="tick">{v}</text>'
        for v in (0, 100, 200, 300, 400))
    xticks = "".join(
        f'<line x1="{x(v):.1f}" y1="{bottom}" x2="{x(v):.1f}" y2="{bottom+5}" stroke="#70808a"/>'
        f'<text x="{x(v):.1f}" y="{bottom+20}" text-anchor="{anchor}" class="tick">{v:,}</text>'
        for v, anchor in ((400, "start"), (1200, "middle"), (3600, "middle"),
                          (6000, "middle"), (12956, "end")))
    dots = "".join(
        f'<circle cx="{x(row["L"]):.1f}" cy="{y(row["correct_nskips"]):.1f}" r="3.6" fill="#315f78"/>'
        f'<circle cx="{x(row["L"]):.1f}" cy="{y(row["null_q99"]):.1f}" r="3.6" fill="#8696a0"/>'
        for row in rows)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 390 358">
<title id="title">Skip-count separation appears at the 6,000-rune ladder point</title>
<desc id="desc">A planted correct key's skip count stays below the wrong-key 1 percent upper-tail threshold through 3,600 runes, then rises above it at 6,000, 9,000 and 12,956 runes.</desc>
<rect width="390" height="358" fill="white"/>
<style>text{{font-family:Arial,Helvetica,sans-serif;fill:#26343e}}.tick{{font-size:11px}}.note{{font-size:12px}}</style>
<text x="19" y="30" font-size="18" font-weight="700">When does the skip count separate?</text>
<line x1="20" y1="52" x2="43" y2="52" stroke="#315f78" stroke-width="3"/>
<text x="49" y="56" class="note">correct key</text>
<line x1="175" y1="52" x2="198" y2="52" stroke="#8696a0" stroke-width="3"/>
<text x="204" y="56" class="note">wrong-key 1% tail</text>
{grid}
<line x1="{x(6000):.1f}" y1="{top}" x2="{x(6000):.1f}" y2="{bottom}" stroke="#b8c4ca" stroke-dasharray="4 4"/>
<polyline points="{poly('null_q99')}" fill="none" stroke="#8696a0" stroke-width="2.5" stroke-linejoin="round"/>
<polyline points="{poly('correct_nskips')}" fill="none" stroke="#315f78" stroke-width="3" stroke-linejoin="round"/>
{dots}
<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#70808a"/>
{xticks}
<text x="{right}" y="323" text-anchor="end" class="note">runes in planted ciphertext · log scale</text>
<text x="19" y="347" class="note">First tested crossing: 6,000; bracket: 3,600–6,000.</text>
</svg>'''
    (HERE / "crossover.svg").write_text(svg + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    make()
