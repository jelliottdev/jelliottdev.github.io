"""Compare within-page trigram matching-pair totals with fixed-count shuffles.

Python 3.12 standard library. Windows overlap; pages never join.
The report includes all observed repeat positions and every simulated page score.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(stream):
    counts = Counter(zip(stream, stream[1:], stream[2:]))
    return sum(count * (count - 1) // 2 for count in counts.values())


def run():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Input changed: " + item["path"])
    alphabet = [r["rune"] for r in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]]
    lookup = {rune: i for i, rune in enumerate(alphabet)}
    streams, observed = [], []
    for page in plan["pages"]:
        text = (ROOT / "text" / (page + ".txt")).read_bytes().decode("utf-8")
        if {c for c in text if "\u16a0" <= c <= "\u16ff"} - set(alphabet):
            raise ValueError("Unknown rune in " + page)
        stream = [lookup[c] for c in text if c in lookup]
        streams.append(stream)
        positions = defaultdict(list)
        for start in range(max(0, len(stream) - 2)):
            positions[tuple(stream[start:start + 3])].append(start)
        observed.append({
            "page": page,
            "rune_count": len(stream),
            "window_count": max(0, len(stream) - 2),
            "matching_pairs": score(stream),
            "repeated_patterns": [
                {"indices": list(pattern), "starts": starts}
                for pattern, starts in sorted(positions.items()) if len(starts) >= 2
            ],
        })
    observed_total = sum(page["matching_pairs"] for page in observed)
    rng = random.Random(plan["seed"])
    trials = []
    for number in range(1, plan["shuffle_trials"] + 1):
        page_scores = []
        for stream in streams:
            shuffled = stream.copy()
            rng.shuffle(shuffled)
            page_scores.append(score(shuffled))
        total = sum(page_scores)
        trials.append({"trial": number, "page_scores": page_scores, "total": total,
                       "at_least_observed": total >= observed_total})
    exceedances = sum(trial["at_least_observed"] for trial in trials)
    probability = (exceedances + 1) / (len(trials) + 1)
    return {
        "schema": "liberpedia-trigram-repeat-null-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "observed": observed,
        "observed_total": observed_total,
        "null_page_order": plan["pages"],
        "null_trials": trials,
        "exceedances": exceedances,
        "monte_carlo_p": probability,
        "threshold": plan["threshold"],
        "below_threshold": probability < plan["threshold"],
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
            raise SystemExit("Rerun differs from saved results.")
        print("All observed repeats and 999 complete-dataset shuffles reproduce.")
    else:
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(result, stream, separators=(",", ":"))
            stream.write("\n")
    print(json.dumps({key: result[key] for key in
                      ["observed_total", "exceedances", "monte_carlo_p", "below_threshold"]}))


if __name__ == "__main__":
    main()
