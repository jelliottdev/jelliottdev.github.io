"""Count emirp-valued archived row sums under the prime-sum baseline's shuffles.

An emirp is prime, has a prime decimal reversal, and is not a palindrome.
Uses Python 3.12 standard library; preserves the baseline's page/trial ordering.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()


def sieve(limit):
    flags = [True] * (limit + 1)
    flags[0] = flags[1] = False
    for divisor in range(2, int(limit ** .5) + 1):
        if flags[divisor]:
            for multiple in range(divisor * divisor, limit + 1, divisor):
                flags[multiple] = False
    return flags


def reverse_decimal(number):
    return int(str(number)[::-1])


def is_emirp(number, flags):
    reverse = reverse_decimal(number)
    return number != reverse and flags[number] and flags[reverse]


def run():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Input changed: " + item["path"])
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    values = {entry["rune"]: entry["prime"] for entry in alphabet}
    pages = []
    for page in plan["pages"]:
        text = (ROOT / "text" / (page + ".txt")).read_bytes().decode("utf-8")
        if {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(values):
            raise ValueError("Unknown rune in " + page)
        rows = []
        for line_number, line in enumerate(text.splitlines(), 1):
            row = [values[c] for c in line if c in values]
            if row:
                rows.append((line_number, row))
        pages.append((page, rows))
    # Cover every possible shuffled row sum and its decimal reversal.
    largest = max(len(row) * max(values.values()) for _, rows in pages for _, row in rows)
    flags = sieve(10 ** len(str(largest)) - 1)
    observed = [
        {"page": page, "rows": [
            {"line": line, "runes": len(row), "sum": sum(row),
             "reverse": reverse_decimal(sum(row)), "prime": flags[sum(row)],
             "emirp": is_emirp(sum(row), flags)}
            for line, row in rows
        ]} for page, rows in pages
    ]
    total = sum(row["emirp"] for page in observed for row in page["rows"])
    rng = random.Random(plan["seed"])
    trials = []
    for number in range(1, plan["shuffle_trials"] + 1):
        emirps, primes = [], []
        for page, rows in pages:
            stream = [value for _, row in rows for value in row]
            rng.shuffle(stream)
            offset, emirp_count, prime_count = 0, 0, 0
            for _, row in rows:
                end = offset + len(row)
                value = sum(stream[offset:end])
                emirp_count += is_emirp(value, flags)
                prime_count += flags[value]
                offset = end
            assert offset == len(stream)
            emirps.append(emirp_count)
            primes.append(prime_count)
        score = sum(emirps)
        trials.append({"trial": number, "page_counts": emirps, "prime_page_counts": primes,
                       "total": score, "at_least_observed": score >= total})
    exceedances = sum(trial["at_least_observed"] for trial in trials)
    probability = (exceedances + 1) / (len(trials) + 1)
    return {
        "schema": "liberpedia-row-emirp-null-v1", "plan_sha256": sha(HERE / "plan.json"),
        "observed": observed, "row_count": sum(len(p["rows"]) for p in observed),
        "emirp_row_count": total, "null_page_order": plan["pages"], "null_trials": trials,
        "exceedances": exceedances, "monte_carlo_p": probability,
        "threshold": plan["threshold"], "below_threshold": probability < plan["threshold"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check", action="store_true")
    choice.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / "results.json").read_text(encoding="utf-8")):
            raise SystemExit("Rerun differs from stored result.")
        print("All row classifications and 999 shuffle trials reproduce exactly.")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, separators=(",", ":"))
            stream.write("\n")
    print(json.dumps({key: result[key] for key in
                      ["row_count", "emirp_row_count", "exceedances", "monte_carlo_p", "below_threshold"]}))


if __name__ == "__main__":
    main()
