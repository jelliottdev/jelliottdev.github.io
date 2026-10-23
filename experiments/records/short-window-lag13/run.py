"""Count exact two-rune recurrences at lag 13 and correct a 2--28 lag scan."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LAGS = range(2, 29)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    lookup = {entry["rune"]: i for i, entry in enumerate(index["alphabet"])}
    pages = []
    hashes = {"data/index.json": digest(ROOT / "data/index.json")}
    for i in range(56):
        path = ROOT / "text" / f"lp2-{i:02d}.txt"
        raw = path.read_text(encoding="utf-8")
        unknown = {c for c in raw if "\u16a0" <= c <= "\u16ff"} - lookup.keys()
        if unknown:
            raise ValueError(f"Unknown runes on page {i}: {unknown}")
        pages.append([lookup[c] for c in raw if c in lookup])
        hashes[f"text/lp2-{i:02d}.txt"] = digest(path)
    assert sum(map(len, pages)) == 12956
    return plan, pages, hashes


def count(pages, lag):
    return sum(page[i] == page[i + lag] and page[i + 1] == page[i + lag + 1]
               for page in pages for i in range(max(0, len(page) - lag - 1)))


def expected_page(page, lag):
    n = len(page)
    opportunities = max(0, n - lag - 1)
    if n < 4 or not opportunities:
        return 0.0
    frequencies = Counter(page).values()
    pairs = [c * (c - 1) for c in frequencies]
    # For lag >= 2 the four positions are distinct. Draw without replacement.
    numerator = sum(c * (c - 1) * (c - 2) * (c - 3) for c in Counter(page).values())
    numerator += sum(pairs) ** 2 - sum(v * v for v in pairs)
    probability = numerator / (n * (n - 1) * (n - 2) * (n - 3))
    return opportunities * probability


def percentile(values, portion):
    ordered = sorted(values)
    return ordered[round(portion * (len(ordered) - 1))]


def report():
    plan, pages, hashes = load()
    expected = {lag: sum(expected_page(page, lag) for page in pages) for lag in LAGS}
    observed = {lag: count(pages, lag) for lag in LAGS}
    ratios = {lag: observed[lag] / expected[lag] for lag in LAGS}
    rng = random.Random(plan["seed"])
    fixed = []
    best = []
    for _ in range(plan["trials"]):
        shuffled = []
        for page in pages:
            copy = page.copy()
            rng.shuffle(copy)
            shuffled.append(copy)
        counts = {lag: count(shuffled, lag) for lag in LAGS}
        fixed.append(counts[13])
        best.append(max(counts[lag] / expected[lag] for lag in LAGS))
    observed_best = max(ratios.values())
    return {"schema": "liberpedia-short-window-lag13-results-v1",
            "plan_sha256": digest(HERE / "plan.json"), "input_sha256": hashes,
            "runes": sum(map(len, pages)),
            "lag13": {"window_length": 15,
                      "windows": sum(max(0, len(page) - 14) for page in pages),
                      "two_pair_matches": observed[13],
                      "exact_page_shuffle_expectation": expected[13],
                      "shuffled_middle_95": [percentile(fixed, .025), percentile(fixed, .975)],
                      "shuffles_at_least_observed": sum(value >= observed[13] for value in fixed)},
            "lag_scan": {"tested_lags": [2, 28],
                         "counts": {str(lag): observed[lag] for lag in LAGS},
                         "expectations": {str(lag): expected[lag] for lag in LAGS},
                         "observed_best_ratio": observed_best,
                         "observed_best_lags": [lag for lag in LAGS if ratios[lag] == observed_best],
                         "lag13_ratio": ratios[13],
                         "shuffled_best_ratio_middle_95": [percentile(best, .025), percentile(best, .975)],
                         "shuffles_best_at_least_observed": sum(value >= observed_best for value in best)},
            "reference": {"trials": plan["trials"], "seed": plan["seed"],
                          "unit": "each entire within-page lag scan rerun after independently shuffling the runes of every page"}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    path = HERE / "results.json"
    if args.check:
        if result != json.loads(path.read_text(encoding="utf-8")):
            raise SystemExit("Saved report differs from recomputation")
        print("PASS short-window lag-13 replay")
    else:
        path.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        print(json.dumps({"lag13": result["lag13"], "lag_scan": result["lag_scan"]}, indent=2))


if __name__ == "__main__":
    main()
