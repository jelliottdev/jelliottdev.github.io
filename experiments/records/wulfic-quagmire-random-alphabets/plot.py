"""Compact source-family decision chart for Stage U."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = (("English runes", "English runes"),
         ("English prime values", "English primes"),
         ("English Latin A-Z", "English A–Z"),
         ("decimal digits", "Decimal digits"),
         ("hex digits", "Hex digits"),
         ("letters A-Z", "Letters A–Z"))
COLORS = {"EXCLUDED": "#35627a", "not excluded": "#7c939f", "untestable": "#dce2e6"}


def render() -> str:
    with (HERE / "source-stage_u_results.tsv").open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream, delimiter="\t") if r["kind"] == "lp2"]
    assert len(rows) == 24
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 400" role="img" aria-labelledby="title desc">',
        '<title id="title">Stage U Quagmire family decisions</title>',
        '<desc id="desc">Six source key-value families, with four tied-or-independent pooled-or-sectioned tests per family. Each bar distinguishes excluded, not excluded and untestable settings.</desc>',
        '<rect width="340" height="400" fill="#f5f6f7"/>',
        '<text x="16" y="29" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#20262b">Quagmire family check</text>',
        '<text x="16" y="52" font-family="Arial,sans-serif" font-size="14" fill="#4a545c">Four source settings per key family</text>',
    ]
    for index, (name, label) in enumerate(NAMES):
        y = 84 + index * 43
        group = [r for r in rows if r["family"] == name]
        assert len(group) == 4
        counts = Counter(r["detail"].split(";", 1)[0] for r in group)
        assert sum(counts.values()) == 4
        out.append(f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" fill="#20262b">{label}</text>')
        x = 143
        for state in ("EXCLUDED", "not excluded", "untestable"):
            width = counts[state] * 35
            if width:
                out.append(f'<rect x="{x}" y="{y-13}" width="{width}" height="17" fill="{COLORS[state]}"/>')
            x += width
        out.append(f'<text x="289" y="{y}" font-family="Arial,sans-serif" font-size="13" fill="#20262b">{counts["EXCLUDED"]}/4</text>')
    out.append('<line x1="16" y1="336" x2="324" y2="336" stroke="#c6cdd2"/>')
    for x, state, label in ((16, "EXCLUDED", "Excluded"), (173, "untestable", "Untestable")):
        out.append(f'<rect x="{x}" y="351" width="12" height="12" fill="{COLORS[state]}"/>')
        out.append(f'<text x="{x+17}" y="362" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">{label}</text>')
    out += ['<text x="16" y="388" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">Conditional family screen, not a decryption.</text>',
            '</svg>']
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    svg = render()
    output = HERE / "comparison.svg"
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == svg
        print("Stage U figure: OK")
    elif not sys.argv[1:]:
        output.write_text(svg, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: plot.py [--check]")
