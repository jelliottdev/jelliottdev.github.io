"""Independent Unicode-block extraction and arithmetic recount for the 1,433 test."""
from collections import Counter
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
alphabet = {row["rune"]: row["index"] for row in
            json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]}


def piece(name, part=None):
    raw = (ROOT / "text" / f"{name}.txt").read_text(encoding="utf-8")
    parts = ["".join(c for c in p if "\u16a0" <= c <= "\u16ff") for p in raw.split("&")]
    parts = [p for p in parts if p]
    return "".join(parts) if part is None else parts[part]


a = ("".join(piece(f"lp1-{n:02}") for n in (14, 15))
     + "".join(piece(f"lp2-{n:02}") for n in range(3, 8))).replace("ᚠ", "")
b = (piece("lp2-33", 1) + "".join(piece(f"lp2-{n:02}") for n in range(34, 39))
     + piece("lp2-39", 0)).replace("ᚠ", "")
c = "".join(piece(f"lp2-{n:02}") for n in range(27, 33))
assert len(a) == len(b) == len(c) == 1433
values = [[alphabet[rune] for rune in stream] for stream in (a, b, c)]


def independent_score(left, right, backward, subtract, shift):
    moved = right[::-1] if backward else right
    moved = moved[shift:] + moved[:shift]
    outputs = [(y - x if subtract else y + x) % 29 for x, y in zip(left, moved)]
    counts = Counter(outputs)
    return sum(count * (count - 1) for count in counts.values())


for pair_name, left, right in zip(
        ("koan-spirals__cuneiform", "koan-spirals__wing-tree", "cuneiform__wing-tree"),
        (values[0], values[0], values[1]), (values[1], values[2], values[2])):
    for name, backwards, subtract in (("add", False, False), ("subtract", False, True),
                                      ("reverse-add", True, False), ("reverse-subtract", True, True)):
        score = independent_score(left, right, backwards, subtract, 0)
        assert saved["observed_variant_scores"][f"{pair_name}:{name}"] == score

rng = random.Random(14333301)
for trial, reported in enumerate(saved["control"]["scores"]):
    shifts = tuple(rng.randrange(1, 1433) for _ in range(3))
    found = max(independent_score(left, right, rev, sub, shifts[pair])
                for pair, (left, right) in enumerate(((values[0], values[1]),
                                                      (values[0], values[2]),
                                                      (values[1], values[2])))
                for rev in (False, True) for sub in (False, True))
    assert found == reported, trial
assert saved["control"]["at_least_observed"] == sum(
    value >= saved["observed_best"] for value in saved["control"]["scores"])
print("PASS: independent stream extraction, twelve observed scores and 999 controls")
