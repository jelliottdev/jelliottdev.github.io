"""Render a compact B-05 fixed-opening result chart."""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGURE = HERE / "b05-opening-funnel.svg"


def render():
    r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    hist = {int(k): v for k, v in r["best_prefix_histogram"].items()}
    rows = [(n, sum(v for k, v in hist.items() if k >= n)) for n in (1, 2, 3, 4, 5, 12)]
    assert rows[-1][1] == r["exact_match_count"] == 0
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 690 325" role="img" aria-labelledby="title desc">',
        '<title id="title">B-05 source keys against fixed LP2 openings</title>',
        '<desc id="desc">Of 70,680 source configurations, 2,503 match at least three runes, 42 at least four, two at least five, and none all twelve.</desc>',
        '<rect width="690" height="325" fill="#f3f5f6"/>',
        '<style>text{font-family:system-ui,-apple-system,Segoe UI,sans-serif;fill:#213444}.head{font-size:19px;font-weight:650}.sub{font-size:13px;fill:#52636d}.tick{font-size:14px}.num{font-size:14px;font-weight:650}</style>',
        '<text class="head" x="26" y="37">B-05 opening matches</text>',
        '<text class="sub" x="26" y="60">Nine 12-rune cribs · 55 page starts · 70,680 source configurations</text>',
    ]
    for i, (n, count) in enumerate(rows):
        y = 83 + 38 * i
        width = 0 if count == 0 else 48 + math.log10(count + 1) / math.log10(70681) * 398
        parts += [
            f'<text class="tick" x="27" y="{y+20}">At least {n} rune{"s" if n != 1 else ""}</text>',
            f'<rect x="181" y="{y}" width="448" height="25" fill="#e2e8eb"/>',
            f'<rect x="181" y="{y}" width="{width:.1f}" height="25" fill="#31627b"/>',
            f'<text class="num" x="660" y="{y+19}" text-anchor="end">{count:,}</text>',
        ]
    parts += ['<text class="sub" x="26" y="315">Log-scale bars; exact counts at right. A fixed opening is an assumption of this test.</text>', '</svg>']
    return "\n".join(parts) + "\n"


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    svg = render()
    if a.check:
        assert FIGURE.read_text(encoding="utf-8") == svg
    else:
        FIGURE.write_text(svg, encoding="utf-8")
    print("Figure matches results" if a.check else FIGURE)


if __name__ == "__main__":
    main()
