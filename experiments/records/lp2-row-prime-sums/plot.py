"""Plot saved null totals and the observed count without rerunning the test."""
import json
import math
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
values = [t["total"] for t in r["null_trials"]]
observed = r["prime_row_count"]
lo = min(min(values), observed) // 5 * 5
hi = (max(max(values), observed) // 5 + 1) * 5
bins = [sum(start <= v < start + 5 for v in values) for start in range(lo, hi, 5)]
assert sum(bins) == len(values)
ymax = math.ceil(max(bins) / 50) * 50


def x(value):
    return 46 + (value - lo) / (hi - lo) * 290


def y(count):
    return 320 - count / ymax * 200


parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 475" role="img" aria-labelledby="title desc">',
    '<title id="title">Prime row sums against shuffled pages</title>',
    '<desc id="desc">Observed count 76 prime-valued row sums out of 594. '
    'The histogram groups 999 shuffled totals in bins of five. '
    '843 totals are at least 76; corrected one-sided p is 0.844.</desc>',
    '<rect width="360" height="475" fill="#faf9f5"/>',
    '<g font-family="sans-serif" fill="#243c48">',
    '<text x="20" y="30" font-size="19">Prime row sums: shuffle comparison</text>',
    '<text x="20" y="54" font-size="13">594 eligible rows across LP2-00–55</text>',
    '<text x="20" y="76" font-size="13">Histogram: 999 shuffles, bins of five counts</text>',
]
for count in range(0, ymax + 1, 50):
    parts.append(
        f'<path d="M46 {y(count):.2f} H336" stroke="#dce0df"/>'
        f'<text x="39" y="{y(count)+4:.2f}" text-anchor="end" font-size="11">{count}</text>'
    )
for start, count in zip(range(lo, hi, 5), bins):
    parts.append(
        f'<rect x="{x(start)+1:.2f}" y="{y(count):.2f}" '
        f'width="{x(start+5)-x(start)-2:.2f}" height="{320-y(count):.2f}" fill="#416879">'
        f'<title>{start}–{start+4}: {count} shuffled datasets</title></rect>'
    )
for value in range(lo, hi + 1, 10):
    parts.append(
        f'<text x="{x(value):.2f}" y="340" text-anchor="middle" font-size="11">{value}</text>'
    )
parts.append(
    f'<path d="M{x(observed):.2f} 110 V320" stroke="#a35328" stroke-width="2"/>'
    f'<text x="{x(observed):.2f}" y="102" text-anchor="middle" font-size="13" '
    f'fill="#a35328">Observed: {observed}</text>'
)
parts.extend([
    '<text x="46" y="364" font-size="13">Prime-valued row sums per dataset</text>',
    f'<text x="20" y="398" font-size="14">{r["exceedances"]} / {len(values)} shuffled totals ≥ observed</text>',
    f'<text x="20" y="423" font-size="14">Corrected one-sided p = {r["monte_carlo_p"]:.3f}</text>',
    '<text x="20" y="452" font-size="13">No evidence of excess under this null model.</text></g></svg>',
])
(HERE / "null-distribution.svg").write_text(
    "".join(parts) + "\n", encoding="utf-8", newline="\n"
)
with (HERE / "observed-rows.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["page", "archived_line", "runes", "prime_sum", "is_prime"])
    for page in r["observed"]:
        for row in page["rows"]:
            writer.writerow([page["page"], row["line"], row["runes"], row["sum"], row["prime"]])
