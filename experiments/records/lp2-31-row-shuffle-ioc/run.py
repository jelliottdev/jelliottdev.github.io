"""LP2-31 periodic-IoC variant with within-row shuffles; Python standard library, no network.

Default prints a summary. --output PATH saves full results without overwriting.
--check recomputes and compares with results.json beside this script.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def scan(symbols, periods):
    rows = []
    for period in periods:
        numerator = denominator = 0
        lengths = []
        for residue in range(period):
            column = symbols[residue::period]
            n = len(column)
            lengths.append(n)
            numerator += sum(c * (c - 1) for c in Counter(column).values())
            denominator += n * (n - 1)
        if not denominator:
            raise ValueError("No within-column pairs")
        rows.append({"period": period, "column_lengths": lengths,
                     "numerator": numerator, "denominator": denominator,
                     "pooled_ioc": numerator / denominator})
    return rows


def maximum(rows):
    return max(Fraction(r["numerator"], r["denominator"]) for r in rows)


def run():
    plan_path = HERE / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    index_path = ROOT / "data/index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    alphabet = {a["rune"] for a in index["alphabet"]}
    source = ROOT / "text" / (plan["page"] + ".txt")
    text = source.read_text(encoding="utf-8")
    if {c for c in text if "\u16a0" <= c <= "\u16ff"} - alphabet:
        raise ValueError("Unrecognized runic code point")
    source_rows = [[c for c in line if c in alphabet] for line in text.splitlines() if line.strip()]
    if any(not row for row in source_rows):
        raise ValueError("Empty rune row")
    symbols = [c for row in source_rows for c in row]
    if plan["offset"] != 0:
        raise ValueError("This implementation supports only offset zero")
    observed = scan(symbols, plan["periods"])
    observed_max = maximum(observed)
    rng = random.Random(plan["seed"])
    null = []
    exceedances = 0
    for trial in range(plan["shuffle_trials"]):
        shuffled = []
        for original in source_rows:
            row = original.copy()
            rng.shuffle(row)
            assert Counter(row) == Counter(original)
            shuffled.extend(row)
        rows = scan(shuffled, plan["periods"])
        peak = maximum(rows)
        exceeds = peak >= observed_max
        exceedances += exceeds
        null.append({"trial": trial + 1,
                     "numerators": [r["numerator"] for r in rows],
                     "max_numerator": peak.numerator, "max_denominator": peak.denominator,
                     "at_least_observed": exceeds})
    p = (1 + exceedances) / (1 + plan["shuffle_trials"])
    return {
        "schema": "liberpedia-periodic-ioc-row-null-v1",
        "inputs": [{"path": p.relative_to(ROOT).as_posix(),
                    "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                   for p in [plan_path, source, index_path]],
        "n": len(symbols), "row_lengths": [len(row) for row in source_rows], "observed": observed,
        "best_periods": [r["period"] for r in observed
                         if Fraction(r["numerator"], r["denominator"]) == observed_max],
        "null_score_encoding": "Numerators align with observed periods and use the same denominators; all period scores are retained exactly.",
        "null_trials": null, "exceedances": exceedances,
        "monte_carlo_p": p, "threshold": plan["threshold"],
        "below_threshold": p < plan["threshold"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--output", type=Path)
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run()
    if args.check:
        saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        if saved != result:
            raise SystemExit("Recomputed result differs; inspect inputs and Python version.")
        print("Full observed and shuffled results reproduce exactly.")
    elif args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
    print(json.dumps({"python": sys.version.split()[0], "n": result["n"],
                      "best_periods": result["best_periods"],
                      "exceedances": result["exceedances"],
                      "monte_carlo_p": result["monte_carlo_p"],
                      "below_threshold": result["below_threshold"]}))


if __name__ == "__main__":
    main()
