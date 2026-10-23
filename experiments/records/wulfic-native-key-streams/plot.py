"""Phone-width score chart comparing LP2 and planted source-model controls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = {
    "K-A primes": "Primes", "K-C word sums": "LP1 word sums",
    "K-D plaintext values": "LP1 rune values", "G-B bytes": "Grid bytes",
    "G-5 5-bit groups": "Grid 5-bit", "G-D base-60 digits": "Grid digits",
}


def build() -> str:
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    streams = [row for stage in report["stages"] for row in stage["streams"]]
    assert len(streams) == 6 and report["total_pass_rows"] == 0
    x = lambda score: 95 + (score + 100) * 217 / 350
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 442" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Six pinned LP2 key streams versus planted controls</title>',
        '<desc id="desc">For each source key, the best LP2 score on at least 100 runes is below zero, while all planted key controls exceed the +30 reading threshold.</desc>',
        '<rect width="340" height="442" fill="#fff"/>',
        '<text x="16" y="27" font-size="17" font-weight="700" fill="#26333a">Key-source replay</text>',
        '<text x="16" y="50" font-size="15" fill="#59676f">Score threshold: +30</text>',
        '<circle cx="22" cy="72" r="5" fill="#285e79"/>',
        '<text x="33" y="77" font-size="15" fill="#26333a">LP2 best</text>',
        '<line x1="149" y1="72" x2="165" y2="72" stroke="#8999a2" stroke-width="5"/>',
        '<text x="173" y="77" font-size="15" fill="#26333a">Planted range</text>',
    ]
    for tick, label in [(-100, "−100"), (0, "0"), (30, "+30"), (100, "+100"), (200, "+200")]:
        xx = x(tick)
        out.append(f'<line x1="{xx:.1f}" y1="104" x2="{xx:.1f}" y2="407" '
                   f'stroke="{"#285e79" if tick == 30 else "#d8dee1"}" '
                   f'stroke-dasharray="{"4 4" if tick == 30 else "2 5"}"/>')
        out.append(f'<text x="{xx:.1f}" y="{98 if tick == 30 else 113}" text-anchor="middle" font-size="15" '
                   f'fill="#59676f">{label}</text>')
    for index, item in enumerate(streams):
        y = 127 + index * 46
        score = float(item["best_at_least_100_runes"]["log_lr_nats"])
        lo, hi = item["positive_score_min"], item["positive_score_max"]
        assert -100 <= score < 30 <= lo <= hi <= 250
        out.append(f'<text x="16" y="{y}" font-size="15" fill="#26333a">{LABELS[item["key"]]}</text>')
        out.append(f'<line x1="{x(lo):.1f}" y1="{y+14}" x2="{x(hi):.1f}" y2="{y+14}" '
                   'stroke="#8999a2" stroke-width="5" stroke-linecap="round"/>')
        out.append(f'<circle cx="{x(score):.1f}" cy="{y+14}" r="5" fill="#285e79"/>')
    out.append('<text x="16" y="425" font-size="15" fill="#59676f">Controls use each key’s available length.</text>')
    out.append('</svg>')
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    chart = build()
    path = HERE / "comparison.svg"
    if args.check:
        assert path.read_text(encoding="utf-8") == chart
        print("Stage I/M score chart: OK")
    else:
        path.write_text(chart, encoding="utf-8", newline="\n")
