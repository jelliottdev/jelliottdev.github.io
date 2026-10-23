"""Render one concrete paired known-key decoder control at phone width."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "decoder-repair-controls.svg"


def render(data):
    pair = data["illustrative_same_message_and_key"]
    assert pair["length"] == 240 and pair["seed"] == 0
    assert [x["mode"] for x in pair["decoders"]] == ["repo_ms3", "drift_l8"]
    old, new = [x["recovery"] for x in pair["decoders"]]
    by_mode = {x["mode"]: x for x in data["by_mode"]}
    assert by_mode["repo_ms3"]["passed"] == 0 and by_mode["drift_l8"]["passed"] == 20
    pieces = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 280" role="img" aria-labelledby="t d">',
        '<title id="t">One known message, same key, two decoders</title>',
        '<desc id="d">On a 240-rune paired-skip planted message, the original beam recovers 45.8 percent of runes while the permissive drift decoder recovers 100 percent. The source gate requires at least 90 percent recovery plus a language score threshold.</desc>',
        '<rect width="320" height="280" fill="#f4f5f6"/>',
        '<g font-family="Arial, sans-serif" fill="#182833">',
        '<text x="15" y="27" font-size="18" font-weight="700">Same message. Same key.</text>',
        '<text x="15" y="48" font-size="13">240 runes · paired key skips · seed 0</text>',
        '<text x="15" y="79" font-size="14" font-weight="700">Original beam</text>',
        '<text x="15" y="134" font-size="14" font-weight="700">Permissive drift</text>',
        '<rect x="15" y="88" width="250" height="22" fill="#d9e0e4"/>',
        f'<rect x="15" y="88" width="{250*old:.2f}" height="22" fill="#69818e"/>',
        '<rect x="15" y="143" width="250" height="22" fill="#d9e0e4"/>',
        f'<rect x="15" y="143" width="{250*new:.2f}" height="22" fill="#32627a"/>',
        f'<text x="270" y="105" font-size="14">{old:.0%}</text>',
        f'<text x="270" y="160" font-size="14">{new:.0%}</text>',
        '<path d="M240 86V171" stroke="#983f42" stroke-width="2" stroke-dasharray="4 4"/>',
        '<text x="15" y="191" font-size="13">Dashed line: 90% recovery gate</text>',
        '<path d="M15 207H305" stroke="#c6d0d5"/>',
        '<text x="15" y="230" font-size="13">Across 20 gated groups per decoder:</text>',
        '<text x="15" y="252" font-size="13">original passed 0 · permissive passed 20</text>',
        '<text x="15" y="271" font-size="13">A pass also needs a readable score.</text>',
        '</g></svg>',
    ]
    return "\n".join(pieces) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    svg = render(data)
    if args.check:
        assert OUT.read_text(encoding="utf-8") == svg
    else:
        OUT.write_text(svg, encoding="utf-8", newline="\n")
    print("PASS mobile SVG", hashlib.sha256(svg.encode()).hexdigest())


if __name__ == "__main__":
    main()
