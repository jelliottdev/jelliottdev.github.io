"""Mobile-first visual: source screen hits sit inside shuffled-search ranges."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent


def chart() -> str:
    result = json.loads((HERE / "results.json").read_text(encoding="utf8"))
    control = result["controls"]["rows"]
    settings = [
        ("Prime-derived streams", result["observed"]["streams"]["source_hits"],
         [r["stream_source_hits"] for r in control]),
        ("Two-value LFSR", result["observed"]["lfsr"]["source_hits"],
         [r["lfsr_source_hits"] for r in control]),
    ]
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 400" role="img" aria-labelledby="t d">',
             '<title id="t">Many source screen hits, no distinct peak</title>',
             '<desc id="d">Observed source-threshold hit counts sit within the ranges from 19 complete searches on within-page shuffled rune orders for both source branches.</desc>',
             '<rect width="340" height="400" fill="#f3f5f7"/>',
             '<text x="18" y="35" font-family="Arial,sans-serif" font-size="19" font-weight="700" fill="#1e2933">Threshold hits are common</text>',
             '<text x="18" y="61" font-family="Arial,sans-serif" font-size="13" fill="#425363">Both branches also find hits in shuffled text.</text>']
    for i, (label, observed, nulls) in enumerate(settings):
        top = 88 + 142 * i
        left, right = 31, 309
        lo, hi = min(nulls + [observed]), max(nulls + [observed])
        span = max(hi - lo, 1)
        # Inset extremes so end labels and markers remain visible.
        xp = lambda value: left + 13 + (right - left - 26) * (value - lo) / span
        obsx = xp(observed); medx = xp(statistics.median(nulls))
        lines += [f'<text x="18" y="{top+21}" font-family="Arial,sans-serif" font-size="16" font-weight="700" fill="#1e2933">{label}</text>',
                  f'<text x="18" y="{top+48}" font-family="Arial,sans-serif" font-size="14" fill="#1e2933">Observed: {observed:,} hits</text>',
                  f'<line x1="{xp(min(nulls)):.1f}" y1="{top+77}" x2="{xp(max(nulls)):.1f}" y2="{top+77}" stroke="#8798a6" stroke-width="10" stroke-linecap="round"/>',
                  f'<line x1="{medx:.1f}" y1="{top+66}" x2="{medx:.1f}" y2="{top+88}" stroke="#324f63" stroke-width="2"/>',
                  f'<circle cx="{obsx:.1f}" cy="{top+77}" r="7" fill="#17668c" stroke="#fff" stroke-width="2"/>',
                  f'<text x="18" y="{top+109}" font-family="Arial,sans-serif" font-size="13" fill="#425363">19 shuffles: {min(nulls):,}–{max(nulls):,} hits</text>']
    lines += ['<circle cx="22" cy="374" r="6" fill="#17668c"/>',
              '<text x="37" y="379" font-family="Arial,sans-serif" font-size="13" fill="#425363">Observed</text>',
              '<line x1="128" y1="374" x2="159" y2="374" stroke="#8798a6" stroke-width="8" stroke-linecap="round"/>',
              '<text x="171" y="379" font-family="Arial,sans-serif" font-size="13" fill="#425363">Shuffled-search range</text>',
              '</svg>']
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = chart().encode("utf8")
    target = HERE / "comparison.svg"
    if args.check:
        assert target.read_bytes() == output
    else:
        target.write_bytes(output)
    print("Source-hit visual verified." if args.check else "Source-hit visual written.")


if __name__ == "__main__":
    main()
