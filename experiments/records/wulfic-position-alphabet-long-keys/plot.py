"""Render a compact summary of Stage W's 50 source decisions."""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = (("hint raw", "Hint"), ("hint-reversed raw", "Hint reversed"),
         ("page_17.bin raw", "File 17"), ("page_21.bin raw", "File 21"),
         ("page_43.bin raw", "File 43"))
COLORS = {"PASS": "#35627a", "EXCLUDED": "#7c939f", "untestable": "#dce2e6"}


def render() -> str:
    with (HERE / "source-stage_w_candidates.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 50
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 320" role="img" '
        'aria-labelledby="title desc">',
        '<title id="title">Stage W decisions by key source</title>',
        '<desc id="desc">Five named byte keys, ten section alignments each. Filled bars count '
        'powered exclusions; pale bars count unresolved settings. No setting is a hit.</desc>',
        '<rect width="340" height="320" fill="#f5f6f7"/>',
        '<text x="16" y="29" font-family="Arial,sans-serif" font-size="18" '
        'font-weight="700" fill="#20262b">Long-key alphabet test</text>',
        '<text x="16" y="52" font-family="Arial,sans-serif" font-size="14" '
        'fill="#4a545c">Excluded of 10 settings per key</text>',
    ]
    for index, (name, label) in enumerate(NAMES):
        y = 84 + index * 43
        counts = Counter(row["verdict"] for row in rows if row["key"] == name)
        assert sum(counts.values()) == 10
        parts.append(f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="15" '
                     f'fill="#20262b">{label}</text>')
        x = 133
        for state in ("PASS", "EXCLUDED", "untestable"):
            width = 17 * counts[state]
            if width:
                parts.append(f'<rect x="{x}" y="{y-14}" width="{width}" height="17" '
                             f'fill="{COLORS[state]}"/>')
            x += width
        parts.append(f'<text x="307" y="{y}" font-family="Arial,sans-serif" font-size="13" '
                     f'fill="#4a545c">{counts["EXCLUDED"]}/10</text>')
    parts.append('<line x1="16" y1="271" x2="324" y2="271" stroke="#c6cdd2"/>')
    for x, state, label in ((16, "EXCLUDED", "Excluded"), (173, "untestable", "Unresolved")):
        parts.append(f'<rect x="{x}" y="286" width="13" height="13" fill="{COLORS[state]}"/>')
        parts.append(f'<text x="{x+19}" y="298" font-family="Arial,sans-serif" font-size="13" '
                     f'fill="#4a545c">{label}</text>')
    parts.append('</svg>\n')
    return "\n".join(parts)


if __name__ == "__main__":
    output = HERE / "comparison.svg"
    expected = render()
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == expected
        print("Stage W figure: OK")
    else:
        output.write_text(expected, encoding="utf-8", newline="\n")
