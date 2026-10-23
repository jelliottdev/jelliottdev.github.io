"""Independently recount the reported lag peak and first ten shuffled-step maxima."""
import json
import math
import random
from pathlib import Path

root = Path(__file__).resolve().parents[3]
here = Path(__file__).resolve().parent
report = json.loads((here / "results.json").read_text(encoding="utf-8"))
index = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
stream = [alphabet[rune] for page in range(3)
          for rune in (root / f"text/lp2-{page:02}.txt").read_text(encoding="utf-8") if rune in alphabet]
assert len(stream) == report["runes"] == 729


def independent_scan(x):
    rows = []
    for lag in range(1, 243):
        overlap = len(x) - lag
        equal = sum(a == b for a, b in zip(x[:overlap], x[lag:]))
        expected = overlap / 29
        standardized = (equal - expected) / math.sqrt(overlap * (1 / 29) * (28 / 29))
        rows.append((equal, standardized))
    return rows


observed = independent_scan(stream)
assert observed[34][0] == report["observed_lag35_equal"] == 42
assert round(observed[34][1], 6) == report["observed_lag35_z"]
assert max(range(242), key=lambda i: observed[i][1]) + 1 == report["observed_best_lag"]
for lag in (35, 70, 105, 140):
    assert observed[lag - 1][0] == report["observed_harmonics"][str(lag)]["equal"]

steps = [(b - a) % 29 for a, b in zip(stream, stream[1:])]
assert {str(k): steps.count(k) for k in range(29)} == report["step_counts"]
rng = random.Random(report["seed"])
for trial in range(10):
    shuffled = steps[:]
    rng.shuffle(shuffled)
    x = [stream[0]]
    for step in shuffled:
        x.append((x[-1] + step) % 29)
    scores = independent_scan(x)
    assert round(max(z for _, z in scores), 6) == report["control_max_z"][trial]
    assert round(scores[34][1], 6) == report["control_lag35_z"][trial]
assert report["max_controls_at_least_observed"] == sum(z >= report["observed_best_z"] for z in report["control_max_z"])
print("lp2-00-02-lag35-selection: independent counts and first ten controls checked")
