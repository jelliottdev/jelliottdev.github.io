#!/usr/bin/env python3
"""Render the finite-key control as an accessible SVG."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "finite-key-control.svg"


def render() -> str:
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    counts = data["finite_independent_key_control"]["ciphertext_doublet_count_distribution"]
    assert counts == [24, 36, 18, 3]
    max_count = max(counts)
    bars = []
    for i, count in enumerate(counts):
        x = 56 + i * 93
        height = round(154 * count / max_count)
        y = 270 - height
        color = "#2d657f" if i == 0 else "#7a8d98"
        bars.append(f'<rect x="{x}" y="{y}" width="58" height="{height}" fill="{color}"/>')
        bars.append(f'<text x="{x + 29}" y="{y - 10}" text-anchor="middle" font-size="14" '
                    f'fill="#233844">{count}/81</text>')
        bars.append(f'<text x="{x + 29}" y="293" text-anchor="middle" font-size="14" '
                    f'fill="#233844">{i}</text>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 440 348" '
            'role="img" aria-labelledby="title desc">\n'
            '<title id="title">An expected floor is not a per-sample minimum</title>\n'
            '<desc id="desc">In a three-symbol example with 81 equally likely independent '
            'keys, 24 produce zero adjacent repeats even though the expected repeat rate '
            'and minimum plaintext difference frequency are one third.</desc>\n'
            '<rect width="440" height="348" fill="#f4f6f7"/>\n'
            '<g font-family="system-ui, -apple-system, Segoe UI, sans-serif">\n'
            '<text x="20" y="32" font-size="17" font-weight="700" fill="#20323c">'
            'A model floor can have lower outcomes</text>\n'
            '<text x="20" y="56" font-size="13" fill="#52626d">'
            'Toy model: 3 symbols · 3 adjacent positions · 81 possible keys</text>\n'
            '<path d="M40 270H406" stroke="#8496a0"/>\n'
            + "\n".join(bars) + '\n'
            '<text x="220" y="320" text-anchor="middle" font-size="14" '
            'fill="#233844">Adjacent repeats in one ciphertext</text>\n'
            '<text x="220" y="340" text-anchor="middle" font-size="12" '
            'fill="#52626d">Expected count: 1 · zero remains possible (24/81)</text>\n'
            '</g></svg>\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    svg = render()
    if args.write:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
    if args.check:
        assert OUT.read_text(encoding="utf-8") == svg
    print("Finite-key SVG ready")


if __name__ == "__main__":
    main()
