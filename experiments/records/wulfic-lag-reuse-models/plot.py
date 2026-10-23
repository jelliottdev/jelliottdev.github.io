"""Compact comparison of the two source pair-law screens."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render(result):
    data = (("AC · key reuse", result["ac"]), ("AD · ciphertext autokey", result["ad"]))
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 411" role="img" aria-labelledby="title desc">',
        '<title id="title">Best AC and AD relation scores</title>',
        '<desc id="desc">Each method has its highest whole-lag, forward-stretch and reverse-stretch score. Every score is below the plus-thirty pass line.</desc>',
        '<rect width="340" height="411" fill="#f6f7f8"/>',
        '<text x="16" y="27" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#263b49">Lag and reuse screens</text>',
        '<text x="16" y="48" font-family="Arial,sans-serif" font-size="13" fill="#52636d">Best score in each search · pass at +30</text>',
    ]
    y = 77
    for title, item in data:
        parts.append(f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" font-weight="700" fill="#263b49">{title}</text>')
        y += 27
        for label, field in (("Whole lag", "F"), ("Forward stretch", "S-forward"), ("Reverse stretch", "S-reverse")):
            score = item["best"][field]
            width = max(0.0, min(1.0, score/30.0)) * 226
            parts += [
                f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#253139">{label}</text>',
                f'<text x="324" y="{y}" text-anchor="end" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#315d74">+{score:.2f}</text>',
                f'<rect x="16" y="{y+7}" width="226" height="7" rx="3" fill="#d6dcdf"/>',
                f'<rect x="16" y="{y+7}" width="{width:.2f}" height="7" rx="3" fill="#315d74"/>',
                f'<line x1="242" y1="{y+4}" x2="242" y2="{y+17}" stroke="#405463" stroke-width="2"/>',
            ]
            y += 40
        y += 9
    parts += [
        '<line x1="16" y1="363" x2="324" y2="363" stroke="#d2d8dc"/>',
        '<text x="16" y="382" font-family="Arial,sans-serif" font-size="13" fill="#52636d">Source controls pass; these maxima do not.</text>',
        '<text x="16" y="402" font-family="Arial,sans-serif" font-size="13" fill="#52636d">AD whole-lag best has only 14 pairs.</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    svg = render(result)
    path = HERE / "comparison.svg"
    if args.check:
        if path.read_text(encoding="utf-8") != svg:
            raise AssertionError("Figure changed relative to result")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
    print("PASS: figure matches result" if args.check else f"Wrote {path}")


if __name__ == "__main__":
    main()
