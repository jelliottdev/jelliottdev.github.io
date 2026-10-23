"""Compact mobile-readable chart for the exact AG/AH source grid."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    stages = {row["stage"]: row for row in result["stages"]}
    assert result["total_candidate_rows"] == 19140 and result["total_pass_rows"] == 0
    assert [(stages[s]["excluded_cells"], stages[s]["keyed_cells"]) for s in ("AG", "AH")] == [
        (270, 300), (324, 360)]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 316" role="img" aria-labelledby="title desc">',
        '<title id="title">Mathematical key streams against LP2</title>',
        '<desc id="desc">No setting passed the source reading threshold. All 594 cells with at least 729 runes were excluded under the tested model. The 66 undecided cells are only nine runes long.</desc>',
        '<rect width="340" height="316" fill="#fff"/>',
        '<text x="16" y="28" font-size="17" font-weight="700" fill="#26333a">Number-stream keys</text>',
        '<text x="16" y="51" font-size="13" fill="#59676f">Pinned source model · 19,140 scored settings</text>',
        '<text x="16" y="93" font-size="14" fill="#26333a">Reached reading threshold</text>',
        '<text x="324" y="93" text-anchor="end" font-size="17" font-weight="700" fill="#285e79">0</text>',
        '<line x1="16" y1="108" x2="324" y2="108" stroke="#d3d9dd"/>',
        '<text x="16" y="142" font-size="14" fill="#26333a">Excluded, sufficient-length cells</text>',
        '<rect x="16" y="156" width="308" height="24" rx="3" fill="#e6eaed"/>',
        '<rect x="16" y="156" width="277.2" height="24" rx="3" fill="#285e79"/>',
        '<text x="16" y="206" font-size="14" fill="#285e79" font-weight="700">594 / 660</text>',
        '<text x="324" y="206" text-anchor="end" font-size="13" fill="#59676f">90%</text>',
        '<line x1="16" y1="222" x2="324" y2="222" stroke="#d3d9dd"/>',
        '<text x="16" y="248" font-size="14" fill="#26333a">66 cells undecided</text>',
        '<text x="16" y="271" font-size="13" fill="#59676f">All are from the nine-rune section 10.</text>',
        '<text x="16" y="298" font-size="13" fill="#59676f">A cell groups 29 shifts of one stream and mode.</text>',
        '</svg>',
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg = build()
    path = HERE / "comparison.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("Wulfic AG/AH figure: OK")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
