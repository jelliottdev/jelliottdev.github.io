"""Draw a phone-readable comparison of LP2 and the conservative planted bound."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build() -> str:
    rows = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["rows"]
    # All values divide by the same unit-specific flat-null mean. A ratio of
    # one means the measured agreement is what random 29-rune output predicts.
    chart = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 340 370" role="img" '
             'aria-labelledby="title desc">',
             '<title id="title">Restart-boundary agreement test</title>',
             '<desc id="desc">Across five boundary types, observed LP2 agreements sit near the flat null '
             'while the lower edge of planted restart controls is much higher.</desc>',
             '<rect width="340" height="370" fill="#fff"/>',
             '<text x="16" y="27" font-size="17" font-weight="700" fill="#252c30">Same-position agreements</text>',
             '<text x="16" y="50" font-size="13" fill="#55636c">Ratio to the random-rune expectation</text>',
             '<rect x="16" y="68" width="14" height="14" fill="#285e79"/>',
             '<text x="36" y="80" font-size="13" fill="#31383d">LP2</text>',
             '<rect x="111" y="68" width="14" height="14" fill="#9eaab2"/>',
             '<text x="131" y="80" font-size="13" fill="#31383d">Planted lower bound</text>',
             '<line x1="120" y1="111" x2="320" y2="111" stroke="#aeb8be"/>',
             '<line x1="220" y1="109" x2="220" y2="332" stroke="#aeb8be" stroke-dasharray="3 4"/>',
             '<text x="118" y="104" font-size="13" fill="#55636c">0</text>',
             '<text x="214" y="104" font-size="13" fill="#55636c">1×</text>',
             '<text x="309" y="104" font-size="13" fill="#55636c">2×</text>']
    for index, row in enumerate(rows):
        y = 141 + index * 44
        observed = row["observed_pairs"] / row["null_mean"]
        planted = min(row["emerson_positive_lower"], row["solved_positive_lower"]) / row["null_mean"]
        chart.append(f'<text x="16" y="{y + 3}" font-size="14" fill="#252c30">{row["unit"].title()}</text>')
        chart.append(f'<rect x="120" y="{y - 11}" width="{100 * observed:.2f}" height="8" fill="#285e79"/>')
        chart.append(f'<rect x="120" y="{y + 2}" width="{100 * planted:.2f}" height="8" fill="#9eaab2"/>')
    chart.extend(['<text x="16" y="358" font-size="13" fill="#55636c">Planted bounds use the weaker of two sources.</text>',
                  '</svg>'])
    return "\n".join(chart) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "comparison.svg"
    svg = build()
    if args.check:
        assert path.read_text(encoding="utf-8") == svg
        print("Stage AB figure: OK")
    else:
        path.write_text(svg, encoding="utf-8", newline="\n")
