"""Bounded prime/Fibonacci positional extraction with shared page-shuffle controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SECTION_IDS = ("warning", "welcome", "some-wisdom", "first-koan", "loss-of-divinity",
               "second-koan", "instruction", "lp2-57")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load() -> tuple[dict, list[list[int]], list[str], dict[str, float], float, list[int]]:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for entry in plan["inputs"]:
        assert sha((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    labels = [row["latin"] for row in alphabet]
    pages = []
    for page in plan["targets"]:
        raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        pages.append([lookup[c] for c in raw if c in lookup])
    counts = {}
    for row in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = row.split()
        counts[gram] = int(amount)
    log_total = math.log10(sum(counts.values()))
    probabilities = {gram: math.log10(n) - log_total for gram, n in counts.items()}
    floor = math.log10(0.01) - log_total
    readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    controls = {row["id"]: row for row in readings["controls"]}
    known = [index for name in SECTION_IDS for page in controls[name]["decoded_pages"]
             for index in page["rune_indices"]]
    return plan, pages, labels, probabilities, floor, known


def prime_positions(length: int) -> list[int]:
    composite = bytearray(length + 1)
    for divisor in range(2, math.isqrt(length) + 1):
        if not composite[divisor]:
            for multiple in range(divisor * divisor, length + 1, divisor):
                composite[multiple] = 1
    return [position - 1 for position in range(2, length + 1) if not composite[position]]


def fibonacci_positions(length: int) -> list[int]:
    positions = []
    previous, current = 1, 2
    while previous <= length:
        positions.append(previous - 1)
        previous, current = current, previous + current
    return positions


def positions(length: int, selector: str) -> list[int]:
    return prime_positions(length) if selector == "prime" else fibonacci_positions(length)


def extract(pages: list[list[int]], arm: str) -> list[list[int]]:
    selector, boundary = arm.rsplit("-", 1) if arm.endswith("-joined") else (arm.split("-")[0], "page-local")
    if boundary == "joined":
        merged = [index for page in pages for index in page]
        return [[merged[index] for index in positions(len(merged), selector)]]
    return [[page[index] for index in positions(len(page), selector)] for page in pages]


def score_segments(segments: list[list[int]], labels: list[str], probabilities: dict[str, float], floor: float) -> tuple[float | None, int, int]:
    total = 0.0
    quads = 0
    latin_characters = 0
    for indices in segments:
        latin = "".join(labels[index] for index in indices)
        latin_characters += len(latin)
        for i in range(max(0, len(latin) - 3)):
            total += probabilities.get(latin[i:i + 4], floor)
            quads += 1
    return (total / quads if quads >= 100 else None, quads, latin_characters)


def arm_results(pages: list[list[int]], plan: dict, labels: list[str], probabilities: dict[str, float], floor: float) -> dict[str, dict]:
    outputs = {}
    for arm in plan["arms"]:
        segments = extract(pages, arm)
        score, quads, characters = score_segments(segments, labels, probabilities, floor)
        outputs[arm] = {"score": score, "latin_quadgrams": quads, "latin_characters": characters,
                        "selected_runes": sum(map(len, segments)),
                        "segment_lengths": [len(segment) for segment in segments]}
    return outputs


def plant(pages: list[list[int]], arm: str, known: list[int], labels: list[str], probabilities: dict[str, float], floor: float) -> dict:
    rng = random.Random(33017120)
    synthetic = [[rng.randrange(29) for _ in page] for page in pages]
    selector = arm.split("-")[0]
    if arm.endswith("joined"):
        merged = [index for page in synthetic for index in page]
        selected = positions(len(merged), selector)
        assert len(selected) <= len(known)
        for position, value in zip(selected, known):
            merged[position] = value
        lengths = [len(page) for page in pages]
        synthetic = []
        start = 0
        for length in lengths:
            synthetic.append(merged[start:start + length])
            start += length
    else:
        selected = []
        cursor = 0
        for page in synthetic:
            for position in positions(len(page), selector):
                selected.append(cursor)
                cursor += 1
                assert cursor <= len(known)
                page[position] = known[cursor - 1]
    recovered = [index for segment in extract(synthetic, arm) for index in segment]
    assert recovered == known[:len(selected)]
    score, quads, _ = score_segments(extract(synthetic, arm), labels, probabilities, floor)
    return {"selected_runes": len(selected), "exact_recovery": True,
            "selected_sha256": sha(bytes(recovered)), "score": score, "latin_quadgrams": quads}


def report() -> dict:
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan, pages, labels, probabilities, floor, known = load()
    observed = arm_results(pages, plan, labels, probabilities, floor)
    extracted = {arm: [{"indices": segment, "latin": "".join(labels[index] for index in segment)}
                       for segment in extract(pages, arm)] for arm in plan["arms"]}
    eligible = [arm for arm in plan["arms"] if observed[arm]["score"] is not None]
    planted = {arm: plant(pages, arm, known, labels, probabilities, floor) for arm in eligible}
    trials = []
    for trial in range(256):
        shuffled = [page.copy() for page in pages]
        rng = random.Random(33017119 + trial)
        for page in shuffled:
            rng.shuffle(page)
        outputs = arm_results(shuffled, plan, labels, probabilities, floor)
        assert [arm for arm in plan["arms"] if outputs[arm]["score"] is not None] == eligible
        trials.append({"seed": 33017119 + trial,
                       "arm_scores": {arm: outputs[arm]["score"] for arm in eligible},
                       "global_max": max(outputs[arm]["score"] for arm in eligible)})
    medians = {arm: sorted(row["arm_scores"][arm] for row in trials)[len(trials) // 2] for arm in eligible}
    for arm in eligible:
        assert planted[arm]["score"] > medians[arm], (arm, planted[arm]["score"], medians[arm])
    best_arm = max(eligible, key=lambda arm: observed[arm]["score"])
    best_score = observed[best_arm]["score"]
    exceeded = sum(row["global_max"] >= best_score for row in trials)
    return {"schema": "liberpedia-prime-fibonacci-extraction-v1", "plan_sha256": sha(plan_bytes),
            "total_page_runes": sum(map(len, pages)), "known_source_runes": len(known),
            "observed": observed, "extracted": extracted, "eligible_arms": eligible, "planted": planted,
            "null_trials": trials, "null_arm_medians": medians,
            "observed_best": {"arm": best_arm, "score": best_score},
            "null_global_at_or_above_observed": exceeded,
            "empirical_global_p": (exceeded + 1) / (len(trials) + 1)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: four selector/boundary arms, 256 shared page shuffles, planted known-reading controls")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"best": result["observed_best"], "at_or_above": result["null_global_at_or_above_observed"],
                          "eligible": result["eligible_arms"]}))
