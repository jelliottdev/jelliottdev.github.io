"""Render the complete fixed-title search as a compact process diagram."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["source_cases"] == 30 and result["source_passes"] == 0
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 295" role="img" aria-labelledby="title desc">',
        '<title id="title">Five square-derived keys yield thirty complete title checks</title>',
        '<desc id="desc">The nine-rune LP2-15 title is tested against five number sequences, two directions and three arithmetic operations. All thirty complete two-word outputs miss the source vocabulary gate.</desc>',
        '<rect width="340" height="295" fill="#f5f6f7"/>',
        '<text x="16" y="30" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#20262b">Square-title test</text>',
        '<text x="16" y="53" font-family="Arial,sans-serif" font-size="14" fill="#4a545c">Fixed LP2-15 header · 4 + 5 runes</text>',
    ]
    boxes = (("5", "key streams"), ("2", "directions"), ("3", "math rules"))
    for i, (number, label) in enumerate(boxes):
        x = 16 + i * 106
        out.extend((
            f'<rect x="{x}" y="76" width="98" height="68" fill="#fff" stroke="#b8c1c7"/>',
            f'<text x="{x+12}" y="108" font-family="Arial,sans-serif" font-size="24" font-weight="700" fill="#35627a">{number}</text>',
            f'<text x="{x+12}" y="129" font-family="Arial,sans-serif" font-size="13" fill="#20262b">{label}</text>',
        ))
    out.extend((
        '<path d="M170 145v29" stroke="#7c939f" stroke-width="2"/>',
        '<path d="M165 169l5 7 5-7" fill="none" stroke="#7c939f" stroke-width="2"/>',
        '<rect x="16" y="185" width="308" height="62" fill="#e6ecef"/>',
        '<text x="30" y="215" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#20262b">30 complete two-word outputs</text>',
        '<text x="30" y="237" font-family="Arial,sans-serif" font-size="14" fill="#4a545c">0 pass the source vocabulary gate</text>',
        '<text x="16" y="278" font-family="Arial,sans-serif" font-size="13" fill="#4a545c">A fixed search, not a general square-cipher verdict.</text>',
        '</svg>',
    ))
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    expected = render()
    output = HERE / "comparison.svg"
    if sys.argv[1:] == ["--check"]:
        assert output.read_text(encoding="utf-8") == expected
        print("Stage I title figure: OK")
    elif not sys.argv[1:]:
        output.write_text(expected, encoding="utf-8", newline="\n")
    else:
        raise SystemExit("Usage: plot.py [--check]")
