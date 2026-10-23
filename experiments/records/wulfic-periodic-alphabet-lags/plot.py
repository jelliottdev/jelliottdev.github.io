"""Mobile-first source-period agreement comparison."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render() -> str:
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    x = lambda rate: 110 + rate * 3000
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 352 398" role="img" aria-labelledby="title desc" font-family="Arial, sans-serif">',
        '<title id="title">Rune agreement at named periodic-alphabet key lengths</title>',
        '<desc id="desc">LP2 agreement at periods 1033, 1729 and 3301 stays near 3.4 to 3.6 percent; even the lowest planted control exceeds 5.2 percent. Exactly 10,030 of 12,935 tested lags meet the source exclusion rule; 2,905 remain open.</desc>',
        '<rect width="352" height="398" fill="#f6f7f8"/>',
        '<text x="16" y="29" fill="#192832" font-size="17" font-weight="700">Periodic alphabets</text>',
        '<text x="16" y="53" fill="#45545f" font-size="15">Same-rune agreement at named lags</text>',
        '<circle cx="21" cy="78" r="5" fill="#2d5e79"/>',
        '<text x="34" y="83" fill="#263741" font-size="15">LP2</text>',
        '<rect x="122" y="72" width="9" height="12" fill="#748d9d"/>',
        '<text x="140" y="83" fill="#263741" font-size="15">Lowest planted rate</text>',
        '<line x1="16" y1="100" x2="336" y2="100" stroke="#ccd3d8"/>',
        '<text x="16" y="125" fill="#45545f" font-size="15">Period</text>',
    ]
    for percent in (0, 2, 4, 6):
        xx = x(percent / 100)
        lines.append(f'<line x1="{xx:.1f}" y1="136" x2="{xx:.1f}" y2="309" stroke="#d5dce0"/>')
        lines.append(f'<text x="{xx:.1f}" y="333" text-anchor="middle" fill="#45545f" font-size="15">{percent}%</text>')
    lines.append(f'<line x1="{x(0.05):.1f}" y1="136" x2="{x(0.05):.1f}" y2="309" stroke="#8aa2b1" stroke-dasharray="4 4"/>')
    for index, row in enumerate(report["named_periods"]):
        y = 170 + index * 66
        observed, planted = x(row["observed_rate"]), x(row["minimum_planted_rate"])
        lines += [
            f'<text x="16" y="{y + 5}" fill="#263741" font-size="15">{row["period"]}</text>',
            f'<line x1="{observed:.1f}" y1="{y}" x2="{planted:.1f}" y2="{y}" stroke="#b8c7d0" stroke-width="3"/>',
            f'<circle cx="{observed:.1f}" cy="{y}" r="6" fill="#2d5e79"/>',
            f'<rect x="{planted - 5:.1f}" y="{y - 7}" width="10" height="14" fill="#748d9d"/>',
            f'<text x="{observed:.1f}" y="{y - 13}" text-anchor="middle" fill="#2d5e79" font-size="15">{row["observed_rate"] * 100:.1f}</text>',
        ]
    lines += [
        '<line x1="16" y1="348" x2="336" y2="348" stroke="#ccd3d8"/>',
        f'<text x="16" y="373" fill="#263741" font-size="15">Excluded: {report["excluded"]:,} lags</text>',
        f'<text x="336" y="373" text-anchor="end" fill="#45545f" font-size="15">Open: {report["open"]:,}</text>',
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
        print("Periodic-alphabet source chart: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
