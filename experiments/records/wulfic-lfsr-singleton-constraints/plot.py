"""Compact mobile-readable picture of how singleton fits grow with L."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def short(n: int) -> str:
    if n < 1000:
        return str(n)
    if n < 1_000_000:
        return f"{n / 1000:.1f}k"
    return f"{n / 1_000_000:.1f}m"


def figure() -> str:
    rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["rows"]
    counts = {(p, l): sum(r["full_singleton_matches"] for r in rows if r["page"] == p and r["length"] == l and r["mode"] in ("sub", "beaufort"))
              for p in ("lp2-28", "lp2-24", "lp2-21") for l in range(1, 6)}
    body = []
    for j, page in enumerate(("lp2-28", "lp2-24", "lp2-21")):
        y = 106 + 44 * j
        body.append(f'<text x="13" y="{y+24}" class="label">{page.upper()}</text>')
        for length in range(1, 6):
            x = 93 + 43 * (length - 1)
            n = counts[page, length]
            strength = 0 if n == 0 else min(1, math.log10(n + 1) / 7)
            # Pure blue-gray scale; darkness represents the number of fitting parameter sets.
            base = (239, 243, 246)
            dark = (90, 138, 163)
            rgb = tuple(round(a + (b - a) * strength) for a, b in zip(base, dark))
            fill = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            body.append(f'<rect x="{x}" y="{y}" width="39" height="34" fill="{fill}" stroke="#cbd4d9"/>')
            body.append(f'<text x="{x+19.5}" y="{y+23}" text-anchor="middle" class="cell">{short(n)}</text>')
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 286" role="img" aria-labelledby="title desc">
<title id="title">Singleton fits grow as the key has more memory</title>
<desc id="desc">Across three LP2 pages, source-defined LFSR streams with one to five memory positions are counted when every visible one-rune word becomes I or A. LP2-28 has just four fits at length five. LP2-21 rises to about 5.8 million parameter fits. These are constraint fits, not decoded readings.</desc>
<style>text{font-family:Arial,Helvetica,sans-serif;fill:#25313a}.title{font-size:16px;font-weight:700}.note{font-size:14px;fill:#53616b}.label,.cell{font-size:14px}.cell{font-weight:700}</style>
<rect x="1" y="1" width="318" height="284" fill="#fff" stroke="#cbd4d9"/>
<text x="13" y="28" class="title">How many streams fit?</text>
<text x="13" y="53" class="note">Every one-rune word must read I or A.</text>
<text x="13" y="82" class="note">Page</text>
<text x="93" y="82" class="note">L1</text><text x="136" y="82" class="note">L2</text><text x="179" y="82" class="note">L3</text><text x="222" y="82" class="note">L4</text><text x="265" y="82" class="note">L5</text>
''' + "\n".join(body) + '''
<line x1="13" y1="249" x2="307" y2="249" stroke="#cbd4d9"/>
<text x="13" y="270" class="note">Fits are candidate settings, not solutions.</text>
</svg>'''


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text = figure()
    path = HERE / "fits.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == text
    else:
        path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
