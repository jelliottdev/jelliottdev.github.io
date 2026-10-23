#!/usr/bin/env python3
"""Compact visual of source ranking versus the missing word evidence."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "comparison.svg"


def render():
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    rows = data["pages"]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 506" role="img" aria-labelledby="title desc">',
        '<title id="title">Every page has a higher best route score but zero matched words</title>',
        '<desc id="desc">For LP2 pages 04 through 13, blue bars show the source maximum bigram score and gray ticks show the untransposed baseline. None of the source outputs matched an English word.</desc>',
        '<rect width="340" height="506" fill="#f6f7f8"/>',
        '<text x="18" y="33" font-family="Arial,sans-serif" font-size="17" font-weight="700" fill="#20272d">Routes raise the source score</text>',
        '<text x="18" y="58" font-family="Arial,sans-serif" font-size="13" fill="#495660">They do not produce a word match.</text>',
        '<text x="69" y="88" font-family="Arial,sans-serif" font-size="12" fill="#495660">Bigram score: baseline → best route</text>',
        '<text x="281" y="88" font-family="Arial,sans-serif" font-size="12" fill="#495660">Words</text>',
    ]
    for i, row in enumerate(rows):
        y = 112 + i * 35
        baseline = row["baseline_score"]
        best = row["best"]["score"]
        bx = 69 + baseline / 5500 * 180
        bw = best / 5500 * 180
        lines.extend([
            f'<text x="18" y="{y+4}" font-family="Arial,sans-serif" font-size="13" fill="#20272d">{row["current_page"].upper()}</text>',
            f'<rect x="69" y="{y-6}" width="{bw:.2f}" height="13" rx="2" fill="#346582"/>',
            f'<line x1="{bx:.2f}" x2="{bx:.2f}" y1="{y-9}" y2="{y+10}" stroke="#20272d" stroke-width="2"/>',
            f'<text x="300" y="{y+4}" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#20272d">0</text>',
        ])
    lines.extend([
        '<line x1="18" x2="322" y1="462" y2="462" stroke="#c9d0d5"/>',
        '<text x="18" y="484" font-family="Arial,sans-serif" font-size="12" fill="#495660">A higher score selects a route; it is not a reading.</text>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n"


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    body = render()
    if args.check:
        assert OUT.read_text(encoding="utf-8") == body
    else:
        OUT.write_text(body, encoding="utf-8", newline="\n")
    print(hashlib.sha256(body.encode()).hexdigest())


if __name__ == "__main__":
    main()
