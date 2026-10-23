#!/usr/bin/env python3
"""Draw the B-05 screen's finding as a compact, responsive SVG."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIGURE = HERE / "result-score.svg"


def xvalue(score: float) -> int:
    return round(62 + (score + 8) * 79)


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    null_max = result["source_null_max"]
    lanes = [
        ("Planted key (control)", -4.17, 106, "#326780"),
        ("Main grid: best case", result["by_part"]["part1"]["best"]["score"], 166, "#536a78"),
        ("Constant shifts: best case", result["by_part"]["shift"]["best"]["score"], 226, "#536a78"),
        ("One-byte variants: best case", result["by_part"]["part2b"]["best"]["score"], 286, "#536a78"),
        ("Highest shuffled reference", null_max, 346, "#8998a1"),
    ]
    body = []
    for label, score, y, color in lanes:
        x = xvalue(score)
        label_x = x - 54 if x > 330 else x + 12
        body += [
            f'<text x="20" y="{y-16}" font-size="15" fill="#20323c">{label}</text>',
            f'<path d="M62 {y}H378" stroke="#c4ced4" stroke-width="2"/>',
            f'<circle cx="{x}" cy="{y}" r="7" fill="{color}"/>',
            f'<text x="{label_x}" y="{y+5}" font-size="14" font-weight="700" fill="{color}">'
            f'{score:.3f}</text>',
        ]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 435" role="img" aria-labelledby="title desc">
  <title id="title">B-05 payload-derived key screen scores</title>
  <desc id="desc">A planted key scored minus 4.17 and passed. The best candidates in all three remaining source searches scored below the required minus 5.5. A shuffled-text reference maximum is shown separately.</desc>
  <rect width="440" height="435" fill="#f4f6f7"/>
  <g font-family="system-ui, -apple-system, Segoe UI, sans-serif">
    <text x="20" y="31" font-size="18" font-weight="700" fill="#20323c">The source grid did not clear the screen</text>
    <text x="20" y="54" font-size="14" fill="#52626d">Higher scores are better · first 400 runes</text>
    <path d="M260 73v292" stroke="#9b5960" stroke-width="2" stroke-dasharray="5 5"/>
    {''.join(body)}
    <path d="M62 385H378M62 379v12M141 379v12M220 379v12M299 379v12M378 379v12" stroke="#82929b" fill="none"/>
    <g fill="#52626d" font-size="13">
      <text x="49" y="406">−8</text><text x="128" y="406">−7</text><text x="207" y="406">−6</text>
      <text x="286" y="406">−5</text><text x="365" y="406">−4</text>
      <text x="146" y="429">Dashed line: required score −5.5</text>
    </g>
  </g>
</svg>\n'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render()
    if args.write:
        FIGURE.write_text(content, encoding="utf-8")
    if args.check:
        assert FIGURE.read_text(encoding="utf-8") == content
    print("B-05 SVG figure ready")


if __name__ == "__main__":
    main()
