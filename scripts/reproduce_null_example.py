#!/usr/bin/env python3
"""Enumerate the null-model guide's fixed AABB teaching example.

Run with Python 3; no packages, manuscript files, network, or randomness needed.
This is intentionally limited to four symbols. It does not test a cipher.
"""
import argparse
from fractions import Fraction
from itertools import permutations
import json


def equal_neighbors(text):
    """Count equal symbols at consecutive positions, without wraparound."""
    return sum(left == right for left, right in zip(text, text[1:]))


def report():
    observed = "AABB"
    # The set removes duplicate permutations of the repeated A and B symbols.
    orders = sorted({"".join(chars) for chars in permutations(observed)})
    rows = []
    for text in orders:
        equal = equal_neighbors(text)
        unequal = len(text) - 1 - equal
        rows.append({"arrangement": text, "equal": equal, "unequal": unequal,
                     "selected": max(equal, unequal)})
    observed_row = next(row for row in rows if row["arrangement"] == observed)
    tails = {}
    for score in ("equal", "selected"):
        threshold = observed_row[score]
        count = sum(row[score] >= threshold for row in rows)
        tails[score] = {"observed_score": threshold, "at_least_observed": count,
                        "total": len(rows), "probability": str(Fraction(count, len(rows)))}
    return {
        "scope": "Synthetic teaching example; not a manuscript experiment.",
        "model": "Equal probability for each distinct arrangement of AABB.",
        "observed": observed,
        "selection_rule": "selected = max(equal neighbors, unequal neighbors)",
        "arrangements": rows,
        "upper_tails_including_ties": tails,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete report as JSON.")
    args = parser.parse_args()
    result = report()
    if args.json:
        print(json.dumps(result, indent=2))
        return
    print(result["scope"])
    print(result["model"])
    print("Arrangement  Equal  Unequal  Selected")
    for row in result["arrangements"]:
        print(f'{row["arrangement"]:11}  {row["equal"]:5}  {row["unequal"]:7}  {row["selected"]:8}')
    print("\nUpper tails include ties and the observed arrangement:")
    for name, tail in result["upper_tails_including_ties"].items():
        print(f'{name}: {tail["at_least_observed"]}/{tail["total"]} = {tail["probability"]}')
    print("Selecting the better pattern changes the comparison, not the input.")


if __name__ == "__main__":
    main()
