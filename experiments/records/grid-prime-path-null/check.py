"""Independent sieve/endpoint check of the prime-path null measurement."""

import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
records = json.loads((ROOT / "exports/alphanumeric-grids.json").read_text(encoding="utf-8"))["records"]
digits = [int(record["token"][0]) for record in records]

sieve = [True] * 3334
sieve[0] = sieve[1] = False
for number in range(2, 58):
    if sieve[number]:
        for multiple in range(number * number, len(sieve), number):
            sieve[multiple] = False
universe = {number for number in range(3334) if sieve[number] and set(str(number)) <= set("0123")}
assert len(universe) == 49


def independent(values):
    eligible = prime_hits = 0
    seen = set()
    # Select endpoint pairs rather than using the producer's start/direction table.
    for start in range(256):
        y, x = divmod(start, 8)
        for end in range(256):
            yy, xx = divmod(end, 8)
            dx, dy = xx - x, yy - y
            if max(abs(dx), abs(dy)) != 3 or dx % 3 or dy % 3:
                continue
            sx, sy = dx // 3, dy // 3
            four = [values[(y + step * sy) * 8 + x + step * sx] for step in range(4)]
            if 4 in four:
                continue
            eligible += 1
            number = sum(digit * 10 ** (3 - step) for step, digit in enumerate(four))
            if sieve[number]:
                prime_hits += 1
                seen.add(number)
    return eligible, prime_hits, len(seen), 49 - len(seen)


assert dict(zip(report["observed"], independent(digits))) == report["observed"]

# Cross-check both shuffle models on a small fixed selection of control grids.
# This checker does not merely compare the producer's saved histograms to itself.
import run
rng = random.Random(48723)
for _ in range(12):
    global_shuffle = digits.copy()
    rng.shuffle(global_shuffle)
    assert independent(global_shuffle) == run.measure(global_shuffle, run.paths(), run.lookup()[1])
    within_rows = []
    for start in range(0, 256, 8):
        row = digits[start:start + 8]
        rng.shuffle(row)
        within_rows.extend(row)
    assert independent(within_rows) == run.measure(within_rows, run.paths(), run.lookup()[1])

for model in report["controls"].values():
    for field, values in model.items():
        histogram = {int(k): v for k, v in values["histogram"].items()}
        assert sum(histogram.values()) == report["replicates_per_control"]
        assert values["minimum"] == min(histogram)
        assert values["maximum"] == max(histogram)
        assert values["count_at_or_below_observed"] == sum(v for k, v in histogram.items() if k <= report["observed"][field])
        assert values["count_at_or_above_observed"] == sum(v for k, v in histogram.items() if k >= report["observed"][field])
print("PASS: independent endpoint/sieve counts, shuffled controls and histogram arithmetic")
