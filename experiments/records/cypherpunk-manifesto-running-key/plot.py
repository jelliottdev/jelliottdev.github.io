"""Render a phone-width whole-page score comparison."""

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULT = json.loads((HERE / "results.json").read_text(encoding="utf-8"))


def x(value):
    return 26 + (value + 7.10) / 0.50 * 268


def render():
    data = {(row["page"], row["variant"]): row for row in RESULT["targets"]}
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 525" role="img" aria-labelledby="title desc">',
        '<title id="title">Cypherpunk manifesto running-key scores</title>',
        '<desc id="desc">On each of three LP2 pages, both tested manifesto key mappings score amid the maxima from sixteen shuffled-key full searches. Blue marks show the manifesto result and gray ranges the shuffled maxima.</desc>',
        '<style>text{font-family:Arial,sans-serif;fill:#24313b}.title{font-size:17px;font-weight:700}.text{font-size:15px}.page{font-size:16px;font-weight:700}</style>',
        '<rect width="320" height="525" fill="#fff"/>',
        '<text x="16" y="25" class="title">Whole-page running-key scores</text>',
        '<text x="16" y="49" class="text">Blue dot: manifesto · gray: 16 shuffled</text>',
        '<text x="16" y="68" class="text">key searches · higher is better →</text>',
    ]
    for tick in (-7.1, -7.0, -6.9, -6.8, -6.7, -6.6):
        out.append(f'<text x="{x(tick):.1f}" y="97" text-anchor="middle" class="text">{tick:.1f}</text>')
    for page_i, page in enumerate(("lp2-00", "lp2-31", "lp2-54")):
        page_y = 124 + 128 * page_i
        out.append(f'<text x="16" y="{page_y}" class="page">{page.upper()}</text>')
        for variant_i, variant in enumerate(("ascii-ordinal", "gp-greedy")):
            row = data[(page, variant)]
            label_y = page_y + 25 + 47 * variant_i
            marker_y = label_y + 19
            best = row["original_top_five"][0]["score"]
            controls = [entry["maximum"] for entry in row["shuffle_maxima"]]
            label = "A–Z shifts" if variant == "ascii-ordinal" else "GP rune key"
            out.extend([
                f'<text x="16" y="{label_y}" class="text">{label} · {best:.2f} · {row["shuffles_at_least_as_high"]}/16 higher</text>',
                f'<line x1="{x(min(controls)):.1f}" y1="{marker_y}" x2="{x(max(controls)):.1f}" y2="{marker_y}" stroke="#9aa6ad" stroke-width="10" stroke-linecap="round"/>',
                f'<circle cx="{x(best):.1f}" cy="{marker_y}" r="7" fill="#315c73"/>',
            ])
    out.extend([
        '<text x="16" y="511" class="text">Planted LP1-04: both mappings rank first.</text>',
        '</svg>\n',
    ])
    return "".join(out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "whole-page-scores.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == render()
    else:
        path.write_text(render(), encoding="utf-8", newline="\n")
    print("Verified figure" if args.check else "Wrote figure")
