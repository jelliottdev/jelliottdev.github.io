"""Mobile-readable summary of the source screen's extrema and pass level."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def draw(result):
    lo, hi = -70.0, 180.0
    def x(value):
        return 30 + (value - lo) * 280 / (hi - lo)
    marks = [
        ("Positive control minimum", result["positive_min"], "#315d74", 81),
        ("Best LP2 candidate", result["candidate_max_rounded"], "#263b49", 147),
        ("Negative control maximum", result["negative_max"], "#7a858d", 213),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 333" role="img" aria-labelledby="title desc">',
        '<title id="title">Stage R detection scores and pass line</title>',
        '<desc id="desc">All source positive controls exceed the pass line; the best LP2 candidate and all negative controls fall below it.</desc>',
        '<rect width="340" height="333" fill="#f6f7f8"/>',
        '<text x="16" y="27" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#263b49">Detection score</text>',
        f'<line x1="{x(30):.1f}" y1="46" x2="{x(30):.1f}" y2="239" stroke="#405463" stroke-width="2" stroke-dasharray="5 4"/>',
        f'<text x="{x(30)+6:.1f}" y="49" font-family="Arial,sans-serif" font-size="13" fill="#405463">Pass +30</text>',
    ]
    for label, value, color, y in marks:
        parts += [
            f'<text x="17" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#253139">{html.escape(label)}</text>',
            f'<text x="323" y="{y}" text-anchor="end" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="{color}">{value:+.2f}</text>',
            f'<line x1="30" y1="{y+16}" x2="310" y2="{y+16}" stroke="#d4d9dc" stroke-width="2"/>',
            f'<circle cx="{x(value):.1f}" cy="{y+16}" r="6" fill="{color}"/>',
        ]
    parts += [
        '<text x="30" y="272" font-family="Arial,sans-serif" font-size="13" fill="#4d5a61">−70</text>',
        '<text x="108" y="272" font-family="Arial,sans-serif" font-size="13" fill="#4d5a61">0</text>',
        '<text x="310" y="272" text-anchor="end" font-family="Arial,sans-serif" font-size="13" fill="#4d5a61">+180</text>',
        '<line x1="16" y1="289" x2="324" y2="289" stroke="#d4d9dc"/>',
        f'<text x="16" y="309" font-family="Arial,sans-serif" font-size="13" fill="#4d5a61">Nine-rune title ceiling: +{result["title_absolute_score_bound"]:.2f}.</text>',
        '<text x="16" y="326" font-family="Arial,sans-serif" font-size="13" fill="#4d5a61">It cannot reach the +30 pass line.</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    svg = draw(result)
    path = HERE / "comparison.svg"
    if args.check:
        if path.read_text(encoding="utf-8") != svg:
            raise AssertionError("Figure differs from measured result")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
    print("PASS: figure matches result" if args.check else f"Wrote {path}")


if __name__ == "__main__":
    main()
