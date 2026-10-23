"""Make a compact mobile-first explanation of the source's failed alignment."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent


def figure() -> str:
    d = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    only = next(x for x in d["paired_regions"] if x["in_bounds"])
    median = statistics.median(d["null"]["maximum_ioc"])
    top = d["pair_screen"]["maximum"]["ioc"]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 320 411" role="img" aria-labelledby="title desc" style="max-width:640px;background:#f5f6f7;font-family:Arial,sans-serif">',
        '<title id="title">The assumed two-time-pad copies do not match</title>',
        '<desc id="desc">Five of six proposed paired regions lie beyond the 8,226-rune source stream. The one in-bounds region has only 7 identical positions among 404. The strongest page-pair difference score is close to the median of shuffled full searches.</desc>',
        '<rect x="1" y="1" width="318" height="409" fill="#f5f6f7" stroke="#d5d9dc"/>',
        '<text x="16" y="31" font-size="19" font-weight="700" fill="#202b32">The copies are not there</text>',
        '<text x="16" y="55" font-size="14" fill="#34434c">Actual source stream: 8,226 runes</text>',
        '<rect x="16" y="72" width="288" height="22" rx="3" fill="#d9e3e8"/>',
        '<rect x="16" y="72" width="14" height="22" fill="#426b80"/>',
        '<rect x="219" y="72" width="14" height="22" fill="#426b80"/>',
        '<text x="16" y="114" font-size="13" fill="#34434c">0–403</text>',
        '<text x="209" y="114" font-size="13" fill="#34434c">5803–6206</text>',
        '<text x="16" y="140" font-size="13" fill="#34434c">The only pair that fits inside it:</text>',
        '<text x="16" y="163" font-size="16" font-weight="700" fill="#202b32">7 of 404 positions identical</text>',
        '<text x="16" y="185" font-size="13" fill="#52616a">Mismatch begins at its first rune.</text>',
        '<line x1="16" y1="203" x2="304" y2="203" stroke="#cbd2d6"/>',
        '<text x="16" y="227" font-size="16" font-weight="700" fill="#202b32">5 other proposed pairs</text>',
        '<text x="16" y="249" font-size="13" fill="#52616a">reach beyond the source stream.</text>',
        '<line x1="16" y1="269" x2="304" y2="269" stroke="#cbd2d6"/>',
        '<text x="16" y="295" font-size="15" font-weight="700" fill="#202b32">Separate page-pair screen</text>',
        '<text x="16" y="319" font-size="13" fill="#34434c">Highest score on LP2</text>',
        f'<text x="300" y="319" text-anchor="end" font-size="14" font-weight="700" fill="#2d617b">{top:.2f}</text>',
        '<text x="16" y="345" font-size="13" fill="#34434c">Shuffled-search median</text>',
        f'<text x="300" y="345" text-anchor="end" font-size="14" font-weight="700" fill="#687983">{median:.2f}</text>',
        f'<text x="16" y="374" font-size="13" fill="#34434c">{d["null"]["maxima_at_least_observed"]} of {d["null"]["replicates"]} shuffled searches</text>',
        '<text x="16" y="394" font-size="13" fill="#34434c">reached the LP2 score or higher.</text>',
        '</svg>',
    ]
    assert only["equal_runes"] == 7 and only["requested_length"] == 404
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "alignment.svg"
    value = figure()
    if args.check:
        assert path.read_text(encoding="utf-8") == value
        print("PASS: mobile figure matches results")
    else:
        path.write_text(value, encoding="utf-8", newline="\n")
        print(f"Saved {path}")
