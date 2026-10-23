"""Render a compact, phone-readable summary of source X2 exclusions."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASSES = ("EN", "RUNES", "HEX", "B64")
LABELS = {"EN": "English", "RUNES": "LP1 runes", "HEX": "Hex digits", "B64": "Base64"}


def render() -> str:
    with (HERE / "source-stage_x_periodic.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    assert len(rows) == 256
    exclusions = {name: sum(r[f"verdict_{name}"] == "EXCLUDED" for r in rows) for name in CLASSES}
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 295" role="img" '
        'aria-labelledby="title desc">',
        '<title id="title">Stage X2 exclusion counts</title>',
        '<desc id="desc">Conditional period-control exclusions among 256 reading-period cells. '
        'English 241, LP1 runes 247, hexadecimal 247, Base64 78.</desc>',
        '<rect width="340" height="295" fill="#f5f6f7"/>',
        '<text x="16" y="29" font-family="Arial,sans-serif" font-size="18" '
        'font-weight="700" fill="#20262b">Periodic byte-model tests</text>',
        '<text x="16" y="52" font-family="Arial,sans-serif" font-size="14" '
        'fill="#4a545c">256 reading × period cells per class</text>',
    ]
    for index, name in enumerate(CLASSES):
        y = 83 + index * 43
        value = exclusions[name]
        parts.extend([
            f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="15" '
            f'fill="#20262b">{LABELS[name]}</text>',
            f'<rect x="124" y="{y-13}" width="174" height="16" fill="#dbe0e4"/>',
            f'<rect x="124" y="{y-13}" width="{174 * value / 256:.1f}" height="16" '
            'fill="#35627a"/>',
            f'<text x="305" y="{y}" font-family="Arial,sans-serif" font-size="15" '
            f'fill="#20262b">{value}</text>',
        ])
    parts.extend([
        '<line x1="16" y1="249" x2="324" y2="249" stroke="#c6cdd2"/>',
        '<text x="16" y="271" font-family="Arial,sans-serif" font-size="13" '
        'fill="#4a545c">No period exceeded the uniform-null maximum.</text>',
        '</svg>\n',
    ])
    return "\n".join(parts)


if __name__ == "__main__":
    output = HERE / "comparison.svg"
    expected = render()
    if len(sys.argv) == 2 and sys.argv[1] == "--check":
        assert output.read_text(encoding="utf-8") == expected
        print("Stage X2 figure: OK")
    else:
        output.write_text(expected, encoding="utf-8", newline="\n")
