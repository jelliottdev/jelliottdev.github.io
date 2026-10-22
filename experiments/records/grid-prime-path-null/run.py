"""Fixed null controls for the LP2 grid's four-cell decimal-prime paths."""

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT / "exports/alphanumeric-grids.json"
PLAN = HERE / "plan.json"
OUTPUT = HERE / "results.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prime(n):
    return n >= 2 and all(n % divisor for divisor in range(2, math.isqrt(n) + 1))


def paths():
    result = []
    for y in range(32):
        for x in range(8):
            for dx, dy in itertools.product((-1, 0, 1), repeat=2):
                if (dx, dy) == (0, 0) or not (0 <= x + 3 * dx < 8 and 0 <= y + 3 * dy < 32):
                    continue
                result.append(tuple((y + step * dy) * 8 + x + step * dx for step in range(4)))
    assert len(result) == 1364
    return result


def lookup():
    universe = sorted({int("".join(map(str, digits)))
                       for digits in itertools.product(range(4), repeat=4)
                       if prime(int("".join(map(str, digits))))})
    assert len(universe) == 49
    position = {value: i for i, value in enumerate(universe)}
    table = [-1] * 625
    for digits in itertools.product(range(4), repeat=4):
        value = digits[0] * 1000 + digits[1] * 100 + digits[2] * 10 + digits[3]
        key = digits[0] * 125 + digits[1] * 25 + digits[2] * 5 + digits[3]
        table[key] = position.get(value, -1)
    return universe, table


def measure(digits, routes, table):
    eligible = hits = mask = 0
    for a, b, c, d in routes:
        key = digits[a] * 125 + digits[b] * 25 + digits[c] * 5 + digits[d]
        if 4 in (digits[a], digits[b], digits[c], digits[d]):
            continue
        eligible += 1
        index = table[key]
        if index >= 0:
            hits += 1
            mask |= 1 << index
    distinct = mask.bit_count()
    return eligible, hits, distinct, 49 - distinct


def report():
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    records = json.loads(SOURCE.read_text(encoding="utf-8"))["records"]
    assert len(records) == 256
    digits = [int(record["token"][0]) for record in records]
    assert set(digits) == set(range(5))
    routes = paths()
    universe, table = lookup()
    names = ["eligible_paths", "prime_occurrences", "distinct_primes", "missing_primes"]
    observed_values = measure(digits, routes, table)
    assert observed_values == (1058, 191, 46, 3)
    observed = dict(zip(names, observed_values))
    rng = random.Random(plan["seed"])
    controls = {}
    for model in ("global_digit_shuffle", "within_row_digit_shuffle"):
        histograms = {name: Counter() for name in names}
        for _ in range(plan["replicates_per_control"]):
            if model == "global_digit_shuffle":
                control = digits.copy()
                rng.shuffle(control)
            else:
                control = []
                for start in range(0, 256, 8):
                    row = digits[start:start + 8]
                    rng.shuffle(row)
                    control.extend(row)
            measured = measure(control, routes, table)
            for name, value in zip(names, measured):
                histograms[name][value] += 1
        n = plan["replicates_per_control"]
        controls[model] = {}
        for name in names:
            hist = histograms[name]
            value = observed[name]
            controls[model][name] = {
                "histogram": {str(key): hist[key] for key in sorted(hist)},
                "minimum": min(hist), "maximum": max(hist),
                "mean": sum(key * count for key, count in hist.items()) / n,
                "count_at_or_below_observed": sum(count for key, count in hist.items() if key <= value),
                "count_at_or_above_observed": sum(count for key, count in hist.items() if key >= value),
                "empirical_lower_tail_plus_one": (1 + sum(count for key, count in hist.items() if key <= value)) / (n + 1),
                "empirical_upper_tail_plus_one": (1 + sum(count for key, count in hist.items() if key >= value)) / (n + 1),
            }
    return {
        "schema": "liberpedia-grid-prime-path-null-v1",
        "question": plan["question"], "plan": PLAN.relative_to(ROOT).as_posix(),
        "plan_sha256": sha256(PLAN), "source": SOURCE.relative_to(ROOT).as_posix(),
        "source_sha256": sha256(SOURCE), "seed": plan["seed"],
        "replicates_per_control": plan["replicates_per_control"],
        "path_count": len(routes), "prime_universe_size": len(universe),
        "observed": observed, "controls": controls,
        "interpretation_limit": "These are conditional digit-shuffle controls for fixed statistics. The exact three missing values were selected after observation; no confirmatory probability for their identity is claimed. Shuffles do not model all plausible cipher constructions or editorial choices."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = (json.dumps(report(), indent=2) + "\n").encode("utf-8")
    if args.check:
        if OUTPUT.read_bytes() != output:
            raise SystemExit("Null-control results differ from the pinned plan or input")
        print("PASS: 10,000 fixed null grids and all four statistics reproduce")
    elif args.write:
        OUTPUT.write_bytes(output)
        print("Wrote", OUTPUT.relative_to(ROOT))
    else:
        print(output.decode("utf-8"), end="")
