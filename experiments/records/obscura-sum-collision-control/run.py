"""Measure how selective the reported OBSCURA word-sum keys are."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
TRIALS = 2000
SEED = 330105


def inputs():
    alphabet_raw = (ROOT / "data/index.json").read_bytes()
    lookup = {entry["rune"]: entry["prime"] for entry in json.loads(alphabet_raw)["alphabet"]}
    source = json.loads((ROOT / "experiments/records/mixed-square-word-sums/results.json").read_text(encoding="utf-8"))
    candidate_rows = source["scope"]["candidates"]
    targets = sorted(set(value for _, value in candidate_rows))
    hashes = {"data/index.json": hashlib.sha256(alphabet_raw).hexdigest(),
              "experiments/records/mixed-square-word-sums/results.json": hashlib.sha256(
                  (ROOT / "experiments/records/mixed-square-word-sums/results.json").read_bytes()).hexdigest()}
    pages = {}
    for n in range(56):
        name = f"lp2-{n:02d}"
        path = f"text/{name}.txt"
        raw = (ROOT / path).read_bytes()
        hashes[path] = hashlib.sha256(raw).hexdigest()
        text = raw.decode("utf-8")
        unknown = {c for c in text if "\u16a0" <= c <= "\u16ff" and c not in lookup}
        if unknown:
            raise ValueError(f"Unknown runes in {path}: {unknown}")
        words = [[lookup[c] for c in part if c in lookup] for part in re.split(r"[-.]", text)]
        pages[name] = [word for word in words if word]
    return candidate_rows, targets, pages, hashes


def counts(pages, targets):
    return Counter(sum(word) for words in pages.values() for word in words if sum(word) in targets)


def shuffled_count(pages, target_set, rng):
    total = 0
    for words in pages.values():
        pool = [value for word in words for value in word]
        rng.shuffle(pool)
        position = 0
        for word in words:
            stop = position + len(word)
            total += sum(pool[position:stop]) in target_set
            position = stop
        assert position == len(pool)
    return total


def calculate():
    candidate_rows, targets, pages, hashes = inputs()
    observed = counts(pages, set(targets))
    observed_total = sum(observed.values())
    rng = random.Random(SEED)
    null = [shuffled_count(pages, set(targets), rng) for _ in range(TRIALS)]
    ordered = sorted(null)
    return {"schema": "liberpedia-obscura-sum-collision-v1", "input_sha256": hashes,
            "source_candidates": candidate_rows, "distinct_sums": targets,
            "word_count": sum(map(len, pages.values())), "observed_total": observed_total,
            "observed_by_sum": {str(value): observed[value] for value in targets},
            "null": {"model": "Shuffle GP prime values within each page, preserving each page's rune inventory and visible word lengths",
                     "seed": SEED, "trials": TRIALS, "mean": sum(null) / TRIALS,
                     "central_95": [ordered[49], ordered[1949]],
                     "at_least_observed": sum(value >= observed_total for value in null),
                     "at_most_observed": sum(value <= observed_total for value in null)},
            "null_counts": null}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = calculate()
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    output = HERE / "results.json"
    if args.check:
        assert output.read_text(encoding="utf-8") == text
        print("Verified", report["observed_total"], "sum collisions and", TRIALS, "page-wise controls")
    else:
        output.write_text(text, encoding="utf-8", newline="\n")
        print(report["observed_total"], report["null"])


if __name__ == "__main__":
    main()
