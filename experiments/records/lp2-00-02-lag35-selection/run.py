"""Retest the published LP2-00–02 lag-35 peak with full-lag selection controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAGES = [f"lp2-{i:02}" for i in range(3)]
LAGS = tuple(range(1, 243))
TRIALS = 999
SEED = 3301


def z_at_lag(values: list[int], lag: int) -> tuple[int, float]:
    n = len(values) - lag
    equal = sum(values[i] == values[i + lag] for i in range(n))
    rate = equal / n
    z = (rate - 1 / 29) / math.sqrt((1 / 29) * (28 / 29) / n)
    return equal, z


def values_from_steps(first: int, steps: list[int]) -> list[int]:
    values = [first]
    for delta in steps:
        values.append((values[-1] + delta) % 29)
    return values


def calculate() -> dict:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    values = [alphabet[c] for page in PAGES
              for c in (ROOT / f"text/{page}.txt").read_text(encoding="utf-8") if c in alphabet]
    assert len(values) == 729
    steps = [(values[i + 1] - values[i]) % 29 for i in range(len(values) - 1)]
    observed = [z_at_lag(values, lag) for lag in LAGS]
    highest = max(range(len(LAGS)), key=lambda i: (observed[i][1], -LAGS[i]))
    rng = random.Random(SEED)
    maxima = []
    lag35 = []
    for _ in range(TRIALS):
        shuffled = steps[:]
        rng.shuffle(shuffled)
        surrogate = values_from_steps(values[0], shuffled)
        zscores = [z_at_lag(surrogate, lag)[1] for lag in LAGS]
        maxima.append(max(zscores))
        lag35.append(zscores[34])
    # Inject a 35-periodic signal through independent replacements as a decoder-power check.
    plant_rng = random.Random(35)
    key = [plant_rng.randrange(29) for _ in range(35)]
    planted = [key[i % 35] if plant_rng.random() >= .55 else plant_rng.randrange(29)
               for i in range(len(values))]
    planted_z = [z_at_lag(planted, lag)[1] for lag in LAGS]
    paths = ["data/index.json"] + [f"text/{page}.txt" for page in PAGES]
    return {
        "schema": "liberpedia-lp2-00-02-lag35-selection-v1",
        "inputs_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
        "runes": len(values), "step_counts": {str(k): steps.count(k) for k in range(29)},
        "scan_lags": [min(LAGS), max(LAGS)],
        "observed_best_lag": LAGS[highest], "observed_best_equal": observed[highest][0],
        "observed_best_z": round(observed[highest][1], 6),
        "observed_lag35_equal": observed[34][0], "observed_lag35_z": round(observed[34][1], 6),
        "observed_harmonics": {str(lag): {"equal": observed[lag - 1][0], "z": round(observed[lag - 1][1], 6)} for lag in (35, 70, 105, 140)},
        "null": "Shuffle the 728 observed modular first differences, retaining their exact inventory and the first rune; repeat the same 242-lag scan.",
        "seed": SEED, "trials": TRIALS,
        "control_max_z": [round(z, 6) for z in maxima],
        "control_lag35_z": [round(z, 6) for z in lag35],
        "max_controls_at_least_observed": sum(z >= observed[highest][1] for z in maxima),
        "fixed_lag35_controls_at_least_observed": sum(z >= observed[34][1] for z in lag35),
        "planted": {"period": 35, "replacement_probability": .55,
                    "lag35_z": round(planted_z[34], 6), "best_lag": LAGS[max(range(len(LAGS)), key=lambda i: planted_z[i])]},
        "all_observed_lags": [{"lag": lag, "equal": observed[lag - 1][0], "z": round(observed[lag - 1][1], 6)} for lag in LAGS],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    target = HERE / "results.json"
    if args.check:
        assert result == json.loads(target.read_text(encoding="utf-8"))
        print("lp2-00-02-lag35-selection: checked")
    else:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print({key: result[key] for key in ("observed_best_lag", "observed_best_z", "max_controls_at_least_observed", "fixed_lag35_controls_at_least_observed", "planted")})


if __name__ == "__main__":
    main()
