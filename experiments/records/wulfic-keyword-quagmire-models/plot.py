"""Visualize the six Stage V families without listing thousands of members."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = {"English runes": "English runes", "English prime values": "English primes",
          "English Latin A-Z": "English A–Z", "decimal digits": "Decimal digits",
          "hex digits": "Hex digits", "letters A-Z": "Letters A–Z"}
COLORS = {"powered_excluded": "#35627a", "powered_open": "#7c939f", "untestable": "#dce2e6"}


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert len(result["family_summaries"]) == 6
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 435" role="img" aria-labelledby="title desc">',
        '<title id="title">Six named-keyword Quagmire family outcomes</title>',
        '<desc id="desc">For each of six source key distributions, the 68-cubed named-alphabet triples are divided into powered exclusions, powered non-exclusions and untestable cases. The first four families are fully excluded; the A-Z family is mostly untestable.</desc>',
        '<rect width="340" height="435" fill="#f5f6f7"/>',
        '<text x="16" y="30" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#20262b">Named alphabet screen</text>',
        '<text x="16" y="53" font-family="Arial,sans-serif" font-size="14" fill="#4a545c">Control-qualified share of each key family</text>',
    ]
    for index, item in enumerate(result["family_summaries"]):
        y = 82 + index * 49
        out.append(f'<text x="16" y="{y}" font-family="Arial,sans-serif" font-size="14" fill="#20262b">{LABELS[item["family"]]}</text>')
        open_width = round(item["powered_open"] * 308 / 314432)
        unknown_width = round(item["untestable"] * 308 / 314432)
        widths = {"powered_excluded": 308 - open_width - unknown_width,
                  "powered_open": open_width, "untestable": unknown_width}
        x = 16
        for key in ("powered_excluded", "powered_open", "untestable"):
            width = widths[key]
            if width:
                out.append(f'<rect x="{x}" y="{y+9}" width="{width}" height="17" fill="{COLORS[key]}"/>')
            x += width
    out.append('<line x1="16" y1="374" x2="324" y2="374" stroke="#c6cdd2"/>')
    for x, key, label in ((16, "powered_excluded", "Excluded"), (122, "powered_open", "Open"),
                          (206, "untestable", "Untestable")):
        out.append(f'<rect x="{x}" y="389" width="12" height="12" fill="{COLORS[key]}"/>')
        out.append(f'<text x="{x+17}" y="400" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">{label}</text>')
    out += ['<text x="16" y="424" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">No source member reaches the lead threshold.</text>',
            '</svg>']
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    svg = render()
    output = HERE / "comparison.svg"
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == svg
        print("Stage V figure: OK")
    elif not sys.argv[1:]:
        output.write_text(svg, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: plot.py [--check]")
