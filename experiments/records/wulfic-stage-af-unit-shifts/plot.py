"""Plot the source's five difference-agreement comparisons on a labelled scale."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build() -> str:
    rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["rows"]
    lo, hi = 0.98, 1.08
    x = lambda value: 120 + (value - lo) * 195 / (hi - lo)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 366" role="img" '
           'aria-labelledby="title desc">',
           '<title id="title">Shifted-restart difference agreements</title>',
           '<desc id="desc">LP2 is near random expectation at five boundaries; all planted lower bounds '
           'lie to the right. Horizontal axis is zoomed from 0.98 to 1.08.</desc>',
           '<rect width="340" height="366" fill="#fff"/>',
           '<text x="16" y="27" font-size="17" font-weight="700" fill="#252c30">Differences within units</text>',
           '<text x="16" y="50" font-size="13" fill="#55636c">Ratio to random-rune expectation</text>',
           '<circle cx="23" cy="76" r="6" fill="#285e79"/>',
           '<text x="37" y="81" font-size="13" fill="#31383d">LP2</text>',
           '<circle cx="112" cy="76" r="6" fill="#9eaab2"/>',
           '<text x="126" y="81" font-size="13" fill="#31383d">Planted lower bound</text>']
    for tick, label in [(0.98, "0.98×"), (1.00, "1.00×"), (1.04, "1.04×"), (1.08, "1.08×")]:
        xx = x(tick)
        out.append(f'<line x1="{xx:.1f}" y1="111" x2="{xx:.1f}" y2="330" '
                   'stroke="#cbd2d5" stroke-dasharray="3 4"/>')
        out.append(f'<text x="{xx:.1f}" y="105" text-anchor="middle" '
                   f'font-size="13" fill="#55636c">{label}</text>')
    for index, row in enumerate(rows):
        y = 143 + index * 44
        actual = row["observed_pairs"] / row["null_mean"]
        planted = min(row["emerson_positive_lower"], row["solved_positive_lower"]) / row["null_mean"]
        assert lo <= actual <= hi and lo <= planted <= hi
        out.append(f'<text x="16" y="{y+5}" font-size="14" fill="#252c30">{row["unit"].title()}</text>')
        out.append(f'<line x1="{x(actual):.1f}" y1="{y}" x2="{x(planted):.1f}" y2="{y}" '
                   'stroke="#bfc9ce" stroke-width="2"/>')
        out.append(f'<circle cx="{x(actual):.1f}" cy="{y}" r="6" fill="#285e79"/>')
        out.append(f'<circle cx="{x(planted):.1f}" cy="{y}" r="6" fill="#9eaab2"/>')
    out.append('<text x="16" y="354" font-size="13" fill="#55636c">Zoomed axis; points are complete-count ratios.</text>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "comparison.svg"
    svg = build()
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("Stage AF figure: OK")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
