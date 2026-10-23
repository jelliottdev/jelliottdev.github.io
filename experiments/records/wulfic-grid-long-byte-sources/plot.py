"""Phone-readable chart of the strongest Stage Y distinct-byte result by source."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = {"page_17.bin": "File 17", "page_21.bin": "File 21", "page_43.bin": "File 43",
          "hint": "Wisdom hint", "page_00-hex": "Page 00 hex", "onion-2-hex": "Onion hex"}


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    rows = result["source_summaries"]
    assert len(rows) == 6 and result["threshold_distinct"] == 120
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 397" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Stage Y byte-source screen</title>',
        '<desc id="desc">The best distinct-byte count from each of six source files lies between 139 and 146. Every one is above the source pass threshold of 120.</desc>',
        '<rect width="340" height="397" fill="#f6f7f8"/>',
        '<text x="16" y="30" fill="#192832" font-size="17" font-weight="700">Grid under six byte sources</text>',
        '<text x="16" y="55" fill="#45545f" font-size="14">Best of every phase, route and operation</text>',
        '<line x1="16" y1="68" x2="324" y2="68" stroke="#cbd4d9"/>',
        '<text x="16" y="91" fill="#45545f" font-size="13">Pass at 120 or fewer distinct bytes</text>',
        '<line x1="171" y1="105" x2="171" y2="335" stroke="#778c99" stroke-width="2" stroke-dasharray="4 4"/>',
    ]
    for i, row in enumerate(rows):
        value = int(row["minimum_distinct"])
        y = 126 + 36 * i
        x = 171 + (value - 120) * 4.2
        lines += [
            f'<text x="16" y="{y + 5}" fill="#263741" font-size="14">{LABELS[row["source"]]}</text>',
            f'<line x1="171" y1="{y}" x2="318" y2="{y}" stroke="#d8dee2"/>',
            f'<circle cx="{x:.1f}" cy="{y}" r="6" fill="#2d5e79"/>',
            f'<text x="324" y="{y + 5}" text-anchor="end" fill="#263741" font-size="14" font-weight="700">{value}</text>',
        ]
    lines += [
        '<line x1="16" y1="340" x2="324" y2="340" stroke="#cbd4d9"/>',
        '<text x="16" y="365" fill="#45545f" font-size="14">All 96 source × route × operation cells</text>',
        '<text x="16" y="385" fill="#45545f" font-size="14">remain above the declared cutoff.</text>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    path = HERE / "comparison.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == content
        print("Stage Y phone chart: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
