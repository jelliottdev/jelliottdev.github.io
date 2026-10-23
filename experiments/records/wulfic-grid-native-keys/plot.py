"""Compact two-screen Stage N score figure for phone widths."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    fraction = result["best_printable_fraction"]
    likelihood = result["best_rune_log_lr"]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 352 302" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Stage N keyed grid screens</title>',
        '<desc id="desc">The best byte result is 42.6 percent printable against a 90 percent source threshold. The best GP29 likelihood is 4.63 nats against a plus-30 source threshold. None of 456 settings passes.</desc>',
        '<rect width="352" height="302" fill="#f6f7f8"/>',
        '<text x="16" y="30" fill="#192832" font-size="17" font-weight="700">Grid with Cicada-derived keys</text>',
        '<text x="16" y="55" fill="#45545f" font-size="15">No source screen passed in 456 settings</text>',
        '<line x1="16" y1="72" x2="336" y2="72" stroke="#ccd3d8"/>',
        '<text x="16" y="99" fill="#263741" font-size="15" font-weight="700">Printable bytes</text>',
        '<text x="16" y="123" fill="#45545f" font-size="15">Best observed</text>',
        f'<text x="336" y="123" text-anchor="end" fill="#263741" font-size="15">{fraction * 100:.1f}%</text>',
        '<rect x="16" y="133" width="320" height="16" rx="2" fill="#c4ccd1"/>',
        f'<rect x="16" y="133" width="{320 * fraction:.1f}" height="16" rx="2" fill="#2d5e79"/>',
        '<line x1="304" y1="129" x2="304" y2="155" stroke="#263741" stroke-width="2"/>',
        '<text x="336" y="172" text-anchor="end" fill="#45545f" font-size="15">Pass at 90%</text>',
        '<line x1="16" y1="185" x2="336" y2="185" stroke="#ccd3d8"/>',
        '<text x="16" y="213" fill="#263741" font-size="15" font-weight="700">Rune likelihood</text>',
        '<text x="16" y="237" fill="#45545f" font-size="15">Best observed</text>',
        f'<text x="336" y="237" text-anchor="end" fill="#263741" font-size="15">{likelihood:.2f}</text>',
        '<rect x="16" y="248" width="320" height="16" rx="2" fill="#c4ccd1"/>',
        f'<rect x="16" y="248" width="{320 * likelihood / 30:.1f}" height="16" rx="2" fill="#2d5e79"/>',
        '<line x1="336" y1="244" x2="336" y2="270" stroke="#263741" stroke-width="2"/>',
        '<text x="336" y="289" text-anchor="end" fill="#45545f" font-size="15">Pass at +30 nats</text>',
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
        print("Stage N phone chart: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
