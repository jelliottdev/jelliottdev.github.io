"""Test three reported 1,433-rune streams under twelve fixed pairwise readings."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PAGE_IDS = ([f"lp1-{n:02}" for n in range(14, 16)]
            + [f"lp2-{n:02}" for n in range(3, 8)]
            + [f"lp2-{n:02}" for n in range(27, 40)])
INPUTS = ["data/index.json", "data/source-snapshots/lp-rune-counts-2026-10-22.csv"] + [
    f"text/{page}.txt" for page in PAGE_IDS]
PAIRINGS = ("koan-spirals__cuneiform", "koan-spirals__wing-tree", "cuneiform__wing-tree")
OPERATIONS = ("add", "subtract", "reverse-add", "reverse-subtract")
TRIALS = 999
SEED = 14333301


def section(page: str, part: int | None, alphabet: dict[str, int]) -> list[int]:
    raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
    pieces = [[alphabet[c] for c in piece if c in alphabet] for piece in raw.split("&")]
    pieces = [piece for piece in pieces if piece]
    if part is not None:
        assert len(pieces) == 2
        return pieces[part]
    return [value for piece in pieces for value in piece]


def streams() -> dict[str, list[int]]:
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {row["rune"]: row["index"] for row in index["alphabet"]}
    assert len(alphabet) == 29 and alphabet["ᚠ"] == 0
    first = [value for page in ["lp1-14", "lp1-15"] + [f"lp2-{n:02}" for n in range(3, 8)]
             for value in section(page, None, alphabet)]
    cuneiform = ([*section("lp2-33", 1, alphabet)]
                 + [value for n in range(34, 39) for value in section(f"lp2-{n:02}", None, alphabet)]
                 + section("lp2-39", 0, alphabet))
    wing = [value for n in range(27, 33) for value in section(f"lp2-{n:02}", None, alphabet)]
    result = {"koan-spirals": [x for x in first if x != 0],
              "cuneiform": [x for x in cuneiform if x != 0],
              "wing-tree": wing}
    assert [len(first), len(cuneiform), len(wing)] == [1464, 1468, 1433]
    assert [first.count(0), cuneiform.count(0), wing.count(0)] == [31, 35, 52]
    assert all(len(s) == 1433 for s in result.values())
    return result


def score(a: list[int], b: list[int], operation: str, shift: int) -> int:
    n = len(a)
    if operation.startswith("reverse"):
        b = b[::-1]
    subtract = operation.endswith("subtract")
    counts = [0] * 29
    for i, value in enumerate(a):
        other = b[(i + shift) % n]
        counts[((other - value) if subtract else (other + value)) % 29] += 1
    return sum(count * (count - 1) for count in counts)


def candidate_scores(values: dict[str, list[int]], shifts: tuple[int, int, int]) -> dict[str, int]:
    pairs = (("koan-spirals", "cuneiform"), ("koan-spirals", "wing-tree"),
             ("cuneiform", "wing-tree"))
    return {f"{PAIRINGS[i]}:{operation}": score(values[left], values[right], operation, shifts[i])
            for i, (left, right) in enumerate(pairs) for operation in OPERATIONS}


def calculate() -> dict:
    values = streams()
    n = 1433
    observed = candidate_scores(values, (0, 0, 0))
    observed_best = max(observed.values())
    rng = random.Random(SEED)
    controls = []
    for _ in range(TRIALS):
        shifts = tuple(rng.randrange(1, n) for _ in range(3))
        controls.append(max(candidate_scores(values, shifts).values()))
    pair_bests = {name: max(value for candidate, value in observed.items()
                            if candidate.startswith(name + ":")) for name in PAIRINGS}
    tail = sum(value >= observed_best for value in controls)
    ordered_pairs = n * (n - 1)
    return {
        "schema": "liberpedia-section-1433-pairing-v1",
        "input_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in INPUTS},
        "construction": {
            "koan-spirals": "LP1-14–15 Koan 2 followed by LP2-03–07 Spirals, omit every F",
            "cuneiform": "LP2-33 second section + LP2-34–38 + LP2-39 first section, omit every F",
            "wing-tree": "LP2-27–32 Wing and Tree, retain F",
        },
        "stream_lengths": {name: len(stream) for name, stream in values.items()},
        "ordered_pair_denominator": ordered_pairs,
        "observed_variant_scores": observed,
        "observed_pair_bests": pair_bests,
        "observed_best": observed_best,
        "observed_best_candidates": [name for name, value in observed.items() if value == observed_best],
        "observed_ioc": round(observed_best / ordered_pairs, 8),
        "control": {
            "seed": SEED, "trials": TRIALS,
            "rule": "For each trial, draw one nonzero circular shift independently for each pair; score all four operations per pair and retain the largest of twelve scores.",
            "scores": controls,
            "at_least_observed": tail,
            "add_one_fraction": f"{tail + 1}/{TRIALS + 1}",
            "best_min": min(controls), "best_median": sorted(controls)[TRIALS // 2],
            "best_max": max(controls),
        },
        "limits": "Conditional on the reported 1,433 equality, streams, F handling, twelve candidates and whole-stream IoC. No discovery-wide probability, key search or language score.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = calculate()
    data = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.write:
        (HERE / "results.json").write_bytes(data)
    if args.check:
        assert (HERE / "results.json").read_bytes() == data
        print("PASS: three 1,433-rune streams, twelve readings and 999 selected-shift controls")
    if not args.check and not args.write:
        print(json.dumps({key: result[key] for key in ("observed_pair_bests", "observed_best", "observed_ioc", "control") if key != "control"}, indent=2))
        print("control: ", {key: result["control"][key] for key in ("at_least_observed", "add_one_fraction", "best_median")})


if __name__ == "__main__":
    main()
