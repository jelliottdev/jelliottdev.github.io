"""Test fixed pairwise subtraction variants for two 2,883-rune LP2 streams."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "experiments/records/spiral-branches-paired-subtraction"
PLAN = BASE / "plan.json"
RESULTS = BASE / "results.json"
STREAMS = BASE / "candidate-streams.json"


def rune_stream(page, alphabet):
    raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
    unknown = {c for c in raw if "\u16a0" <= c <= "\u16ff"} - set(alphabet)
    if unknown:
        raise ValueError(f"Unknown runes on {page}: {unknown}")
    return [(alphabet[c], page, ordinal) for ordinal, c in
            enumerate(c for c in raw if c in alphabet)]


def build_inputs(plan):
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {entry["rune"]: entry["index"] for entry in index["alphabet"]}
    assert sorted(alphabet.values()) == list(range(29)) and alphabet["ᚠ"] == 0
    first = [item for number in range(3, 8) for item in rune_stream(f"lp2-{number:02}", alphabet)]
    branches = [item for number in range(8, 15) for item in rune_stream(f"lp2-{number:02}", alphabet)]
    title_text = (ROOT / "text/lp2-15.txt").read_text(encoding="utf-8").split("&", 1)[0]
    title = [(alphabet[c], "lp2-15", ordinal) for ordinal, c in
             enumerate(c for c in title_text if c in alphabet)]
    b_pages = []
    for number in range(40, 54):
        b_pages.append([item for item in rune_stream(f"lp2-{number:02}", alphabet) if item[0] != 0])
    second = [item for page in b_pages for item in page]
    assert (len(first), len(branches), len(title), len(second)) == (1145, 1729, 9, 2883)
    for label, items in [("spirals", first), ("branches_and_title", branches + title)]:
        by_index = {entry["index"]: entry["rune"] for entry in index["alphabet"]}
        digest = hashlib.sha256("".join(by_index[item[0]] for item in items).encode("utf-8")).hexdigest()
        assert digest == plan["posted_stream_sha256"][label]
    return first, branches, title, b_pages, second, index["alphabet"]


def variants(first, branches, title):
    transform = lambda items: [(28 - value, page, ordinal) for value, page, ordinal in items]
    return {
        "direct": first + branches + title,
        "reverse-branches": first + list(reversed(branches)) + title,
        "reverse-tail": first + list(reversed(branches + title)),
        "atbash-branches": first + transform(branches) + title,
        "atbash-tail": first + transform(branches + title),
    }


def pairs(output):
    counts = Counter(output)
    return sum(n * (n - 1) for n in counts.values())


def score(b, a):
    return pairs((value - other) % 29 for value, other in zip(b, a))


def analyze():
    plan_bytes = PLAN.read_bytes()
    plan = json.loads(plan_bytes)
    first, branches, title, b_pages, second, alphabet = build_inputs(plan)
    candidate = variants(first, branches, title)
    assert list(candidate) == plan["variants"]
    n = len(second)
    b = [item[0] for item in second]
    a_values = {name: [item[0] for item in items] for name, items in candidate.items()}
    observed = {name: score(b, values) for name, values in a_values.items()}
    denominator = n * (n - 1)
    observed_max = max(observed.values())
    shifts = []
    for offset in range(1, n):
        rotated = b[offset:] + b[:offset]
        shifts.append(max(score(rotated, values) for values in a_values.values()))
    rng = random.Random(plan["shuffle_seed"])
    shuffles = []
    for _ in range(plan["shuffle_trials"]):
        changed = []
        for page in b_pages:
            values = [item[0] for item in page]
            rng.shuffle(values)
            changed.extend(values)
        shuffles.append(max(score(changed, values) for values in a_values.values()))
    index_to_rune = {entry["index"]: entry["rune"] for entry in alphabet}
    candidate_streams = {
        "schema": "liberpedia-paired-subtraction-streams-v1",
        "b_without_f": [{"value": value, "page": page, "page_rune_ordinal_zero_based": ordinal}
                        for value, page, ordinal in second],
        "variants": {name: {
            "a": [{"value": value, "page": page, "page_rune_ordinal_zero_based": ordinal}
                  for value, page, ordinal in items],
            "output_runes": "".join(index_to_rune[(b[i] - items[i][0]) % 29] for i in range(n)),
        } for name, items in candidate.items()},
    }
    streams_bytes = (json.dumps(candidate_streams, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return {
        "schema": "liberpedia-paired-subtraction-results-v1",
        "plan_sha256": hashlib.sha256(plan_bytes).hexdigest(),
        "source_lengths": {"spirals": len(first), "branches": len(branches),
                           "pre_mobius_title": len(title), "spiral_branches_without_f": n},
        "score": "ordered equal-symbol pairs / 2883×2882; larger means greater whole-stream index of coincidence",
        "denominator": denominator,
        "observed_pair_counts": observed,
        "observed_max_pair_count": observed_max,
        "winning_variants": [name for name, value in observed.items() if value == observed_max],
        "controls": {
            "nonzero_circular_shifts": {"maxima": shifts,
                                        "tail_count": sum(value >= observed_max for value in shifts),
                                        "comparison_fraction": f"{1 + sum(value >= observed_max for value in shifts)}/{n}"},
            "within_page_shuffle": {"seed": plan["shuffle_seed"], "maxima": shuffles,
                                    "tail_count": sum(value >= observed_max for value in shuffles),
                                    "comparison_fraction": f"{1 + sum(value >= observed_max for value in shuffles)}/{len(shuffles) + 1}"},
        },
        "candidate_streams_sha256": hashlib.sha256(streams_bytes).hexdigest(),
        "limits": "A new implementation of suggested operations, not a historical output replay. Fixed five variants and whole-stream IoC only; neither n-gram scores nor other arithmetic operators are tested. Conditional controls do not correct for the earlier discovery of equal section lengths or all possible transformations.",
    }, streams_bytes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result, stream_bytes = analyze()
    output = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.write:
        RESULTS.write_bytes(output)
        STREAMS.write_bytes(stream_bytes)
    if args.check:
        assert RESULTS.read_bytes() == output
        assert STREAMS.read_bytes() == stream_bytes
        print("PASS: five paired-subtraction variants and both complete controls")
    if not (args.check or args.write):
        print(json.dumps({"observed_pair_counts": result["observed_pair_counts"],
                          "control_fractions": {name: item["comparison_fraction"] for name, item in result["controls"].items()}}, indent=2))
