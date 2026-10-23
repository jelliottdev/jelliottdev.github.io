"""Two exact fixed-key branches from a pinned C++ draft; standard library only."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
INPUTS = {row["path"]: row["sha256"] for row in PLAN["inputs"]}
KEY = [ord(c) - 65 for c in PLAN["key"]]
F = ord("F") - 65


def source(relative):
    raw = (ROOT / relative).read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUTS[relative]:
        raise ValueError(f"Pinned input changed: {relative}")
    return raw


def plus(text, keep_f=False):
    out = []
    for i, char in enumerate(text):
        value = ord(char) - 65
        assert 0 <= value < 26
        out.append("F" if keep_f and value == F else chr(65 + (value + KEY[i % len(KEY)]) % 26))
    return "".join(out)


def ordinary_minus(text):
    return "".join(chr(65 + (ord(char) - 65 - KEY[i % len(KEY)]) % 26)
                   for i, char in enumerate(text))


def forbidden_at(i):
    key = KEY[i % len(KEY)]
    return None if key == 0 else chr(65 + (F + key) % 26)


def forbidden_positions(text):
    return [i for i, char in enumerate(text) if char == forbidden_at(i)]


def setup():
    alphabet = json.loads(source("data/index.json"))["alphabet"]
    lookup = {item["rune"]: i for i, item in enumerate(alphabet)}
    latin = [item["latin"] for item in alphabet]
    assert len(latin) == 29 and all(x and x.isascii() and x.isupper() for x in latin)
    lines = source("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()
    counts = {gram: int(count) for gram, count in (line.split() for line in lines)}
    total = sum(counts.values())
    log_total = math.log10(total)
    weights = {gram: math.log10(count) - log_total for gram, count in counts.items()}
    floor = math.log10(0.01) - log_total

    def score(text):
        assert len(text) >= 4 and text.isascii() and text.isupper()
        return sum(weights.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)

    def expand(indices):
        return "".join(latin[x] for x in indices)

    return lookup, score, expand


def controls(score, expand):
    fixture = PLAN["source_parity_fixture"]
    assert plus(fixture["input"]) == fixture["ordinary_plus"]
    assert plus(fixture["input"], True) == fixture["f_preserving_plus"]
    collision = PLAN["collision_control"]
    assert [plus(s, True) for s in collision["inputs"]] == [collision["f_preserving_plus"]] * 2
    assert len(KEY) == 11 and PLAN["period"] == 11 and PLAN["phase"] == 0
    slot_controls = []
    for slot in range(len(KEY)):
        actual = {plus("A" * slot + chr(65 + x), True)[-1] for x in range(26)}
        blocked = forbidden_at(slot)
        expected = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - ({blocked} if blocked else set())
        assert actual == expected
        assert all(slot not in forbidden_positions("A" * slot + char)
                   for char in actual)
        slot_controls.append({"slot": slot, "key": PLAN["key"][slot], "forbidden": blocked,
                              "image_size": len(actual), "exhaustive_pass": True})
    readings = []
    cfg = PLAN["english_controls"]
    for number, name in enumerate(PLAN["readings"]):
        rows = csv.DictReader(source(f"exports/readings/{name}.csv").decode("utf-8-sig").splitlines())
        indices = [int(row["output_index"]) for row in rows][:cfg["length_runes"]]
        assert len(indices) == cfg["length_runes"]
        plain = expand(indices)
        cipher = plus(plain)
        assert ordinary_minus(cipher) == plain
        direct = score(plain)
        below = 0
        for rep in range(cfg["shuffle_replicates_per_reading"]):
            shuffled = indices.copy()
            random.Random(cfg["shuffle_seed"] + 1000 * number + rep).shuffle(shuffled)
            below += score(expand(shuffled)) < direct
        readings.append({"reading": name, "latin_length": len(plain), "source_score": direct,
                         "shuffle_scores_below": below, "ordinary_plant_exact": True})
    good = sum(r["source_score"] >= cfg["score_threshold"] and
               r["shuffle_scores_below"] >= 198 for r in readings)
    return {"source_fixture_pass": True, "collision_confirmed": True,
            "all_slot_images_exact": all(r["exhaustive_pass"] for r in slot_controls),
            "slots": slot_controls, "readings": readings, "good_originals": good,
            "ordinary_plants_exact": len(readings), "passed": good >= cfg["required_originals"]}


def produce(control_only=False):
    lookup, score, expand = setup()
    gate = controls(score, expand)
    if control_only:
        return gate
    if not gate["passed"]:
        raise ValueError("Predeclared English-control gate failed; LP2 not scored")
    pages = []
    for name in PLAN["pages"]:
        data = json.loads(source(f"data/pages/{name}.json"))
        indices = [lookup[r] for line in data["lines"] for r in line["raw"] if r in lookup]
        assert len(indices) == data["rune_count"] and indices
        pages.append((name, indices))
    assert len(pages) == 55
    assert json.loads(source("data/pages/lp2-50.json"))["rune_count"] == 0
    outcomes = []
    for name, indices in pages:
        text = expand(indices)
        bad = forbidden_positions(text)
        plain = ordinary_minus(text)
        outcomes.append({"page": name, "runes": len(indices), "latin_characters": len(text),
                         "f_forbidden_count": len(bad), "f_first_forbidden_index": bad[0] if bad else None,
                         "f_image_possible": not bad, "ordinary_score": score(plain),
                         "ordinary_decoded_latin": plain,
                         "ordinary_decoded_sha256": hashlib.sha256(plain.encode("ascii")).hexdigest()})
    null_maxima = []
    cfg = PLAN["global_null"]
    for rep in range(cfg["replicates"]):
        best = -math.inf
        for page_number, (_, indices) in enumerate(pages):
            shuffled = indices.copy()
            random.Random(cfg["seed"] + 1000 * rep + page_number).shuffle(shuffled)
            best = max(best, score(ordinary_minus(expand(shuffled))))
        null_maxima.append(best)
    best = max(outcomes, key=lambda row: row["ordinary_score"])
    tail = sum(value >= best["ordinary_score"] for value in null_maxima)
    return {"schema": "liberpedia-eternalth-vigenere-results-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "control_gate": gate, "page_count": len(outcomes), "outcomes": outcomes,
            "f_possible_pages": [row["page"] for row in outcomes if row["f_image_possible"]],
            "best_ordinary_page": best["page"], "best_ordinary_score": best["ordinary_score"],
            "ordinary_threshold_passes": sum(row["ordinary_score"] >= PLAN["english_controls"]["score_threshold"]
                                             for row in outcomes),
            "null_maxima": null_maxima, "null_at_least_best": tail,
            "empirical_global_tail": (tail + 1) / (len(null_maxima) + 1)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls-only", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = produce(args.controls_only)
    if args.controls_only:
        print(json.dumps({key: report[key] for key in ("passed", "good_originals", "ordinary_plants_exact", "all_slot_images_exact")}))
    elif args.check:
        assert report == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("Pinned inputs, source controls, page checks, and full null match saved results")
    else:
        (HERE / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({key: report[key] for key in ("page_count", "f_possible_pages", "best_ordinary_page", "best_ordinary_score", "ordinary_threshold_passes", "null_at_least_best")}))
