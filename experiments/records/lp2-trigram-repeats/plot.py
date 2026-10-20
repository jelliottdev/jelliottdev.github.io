"""Render a mobile-width histogram and page CSV from the saved report."""
from collections import Counter
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
values = [trial["total"] for trial in r["null_trials"]]
observed = r["observed_total"]
lo = min(min(values), observed) // 5 * 5
hi = (max(max(values), observed) // 5 + 1) * 5
bins = Counter(value // 5 * 5 for value in values)
ymax = math.ceil(max(bins.values()) / 50) * 50
x = lambda value: 46 + (value - lo) / (hi - lo) * 290
y = lambda count: 320 - count / ymax * 200
parts = [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 475" role="img" aria-labelledby="title desc">',
    '<title id="title">Within-page matching trigram pairs</title>',
    f'<desc id="desc">Observed total {observed}. Histogram of 999 shuffled datasets. '
    f'{r["exceedances"]} totals meet or exceed the observation; corrected upper-tail p is {r["monte_carlo_p"]:.3f}.</desc>',
    '<rect width="360" height="475" fill="#faf9f5"/><g font-family="sans-serif" fill="#243c48">',
    '<text x="20" y="30" font-size="19">Repeated three-rune windows</text>',
    '<text x="20" y="54" font-size="13">Within-page matching pairs, summed over LP2</text>',
    '<text x="20" y="76" font-size="13">999 shuffles; histogram bins contain five counts</text>',
]
for count in range(0, ymax + 1, 50):
    parts.append(f'<path d="M46 {y(count):.2f} H336" stroke="#dce0df"/><text x="39" y="{y(count)+4:.2f}" text-anchor="end" font-size="11">{count}</text>')
for start in range(lo, hi, 5):
    count = bins[start]
    parts.append(f'<rect x="{x(start)+1:.2f}" y="{y(count):.2f}" width="{x(start+5)-x(start)-2:.2f}" height="{320-y(count):.2f}" fill="#416879"><title>{start}–{start+4}: {count} datasets</title></rect>')
for value in range(lo, hi + 1, 10):
    parts.append(f'<text x="{x(value):.2f}" y="340" text-anchor="middle" font-size="11">{value}</text>')
parts.extend([
    f'<path d="M{x(observed):.2f} 110 V320" stroke="#a35328" stroke-width="2"/>',
    f'<text x="{x(observed):.2f}" y="102" text-anchor="middle" font-size="13" fill="#a35328">Observed: {observed}</text>',
    '<text x="46" y="364" font-size="13">Matching trigram pairs per full dataset</text>',
    f'<text x="20" y="398" font-size="14">{r["exceedances"]} / 999 shuffled totals ≥ observed</text>',
    f'<text x="20" y="423" font-size="14">Corrected upper-tail p = {r["monte_carlo_p"]:.3f}</text>',
    '<text x="20" y="452" font-size="13">Scope: LP2-00–55; overlapping windows</text></g></svg>\n',
])
(HERE / "null-distribution.svg").write_text("".join(parts), encoding="utf-8", newline="\n")
with (HERE / "observed-pages.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(["page", "rune_count", "window_count", "matching_pairs", "distinct_repeated_patterns"])
    for page in r["observed"]:
        writer.writerow([page["page"], page["rune_count"], page["window_count"],
                         page["matching_pairs"], len(page["repeated_patterns"])])
