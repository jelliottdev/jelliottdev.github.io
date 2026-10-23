"""Direct GP29 readings of per-line and per-word manuscript counts."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE_IDS = ("line-runes", "word-runes")
MAPPINGS = ("count", "count-minus-one")
BOUNDARIES = ("page-local", "joined")


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_counts(raw: str, runes: set[str]) -> dict[str, list[int]]:
    line_counts = [sum(char in runes for char in line) for line in raw.splitlines()]
    line_counts = [number for number in line_counts if number]
    joined_layout = raw.replace("/", "").replace("\n", "")
    word_counts = [sum(char in runes for char in part) for part in joined_layout.split("-")]
    word_counts = [number for number in word_counts if number]
    return {"line-runes": line_counts, "word-runes": word_counts}


def load():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    for entry in plan["inputs"]:
        assert sha((ROOT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    runes = {entry["rune"] for entry in alphabet}
    labels = [entry["latin"] for entry in alphabet]
    pages = [source_counts((ROOT / f"text/{page}.txt").read_text(encoding="utf-8"), runes)
             for page in plan["targets"]]
    count_table = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        count_table[gram] = int(amount)
    divisor = math.log10(sum(count_table.values()))
    model = {gram: math.log10(amount) - divisor for gram, amount in count_table.items()}
    floor = math.log10(0.01) - divisor
    readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    by_id = {section["id"]: section for section in readings["controls"]}
    known = [index for name in plan["source_reading_ids"] for page in by_id[name]["decoded_pages"]
             for index in page["rune_indices"]]
    return plan, plan_bytes, pages, labels, model, floor, known


def gp_index(number: int, mapping: str) -> int:
    return (number if mapping == "count" else number - 1) % 29


def score_segments(segments: list[list[int]], labels: list[str], model: dict[str, float], floor: float):
    total = 0.0
    quads = 0
    latin_characters = 0
    for indices in segments:
        latin = "".join(labels[index] for index in indices)
        latin_characters += len(latin)
        for position in range(len(latin) - 3):
            total += model.get(latin[position:position + 4], floor)
            quads += 1
    return total / quads if quads >= 100 else None, quads, latin_characters


def outputs(pages, labels, model, floor):
    rows = {}
    for source in SOURCE_IDS:
        for mapping in MAPPINGS:
            page_indices = [[gp_index(value, mapping) for value in page[source]] for page in pages]
            for boundary in BOUNDARIES:
                identifier = f"{source}-{mapping}-{boundary}"
                segments = page_indices if boundary == "page-local" else [[index for page in page_indices for index in page]]
                score, quads, chars = score_segments(segments, labels, model, floor)
                rows[identifier] = {"score": score, "latin_quadgrams": quads, "latin_characters": chars,
                                    "events": sum(map(len, segments)), "segments": segments,
                                    "latin_segments": ["".join(labels[index] for index in segment) for segment in segments]}
    return rows


def planted(pages, known, labels, model, floor):
    controls = {}
    for source in SOURCE_IDS:
        for mapping in MAPPINGS:
            count = 0
            synthetic = []
            for page in pages:
                values = []
                for _ in page[source]:
                    index = known[count % len(known)]
                    values.append(index if (mapping == "count" and index > 0) else
                                  29 if mapping == "count" else index + 1)
                    count += 1
                synthetic.append(values)
            recovered = [[gp_index(number, mapping) for number in page] for page in synthetic]
            expected = [known[position % len(known)] for position in range(count)]
            assert [index for page in recovered for index in page] == expected
            for boundary in BOUNDARIES:
                segments = recovered if boundary == "page-local" else [[index for page in recovered for index in page]]
                value, quads, _ = score_segments(segments, labels, model, floor)
                assert value is not None and value > -5.5
                controls[f"{source}-{mapping}-{boundary}"] = {"score": value, "events": count,
                                                               "latin_quadgrams": quads, "exact_recovery": True}
    return controls


def report():
    plan, plan_bytes, pages, labels, model, floor, known = load()
    observed = outputs(pages, labels, model, floor)
    assert list(observed) == plan["arms"]
    controls = planted(pages, known, labels, model, floor)
    eligible = [name for name in plan["arms"] if observed[name]["score"] is not None]
    assert len(eligible) == 8
    trials = []
    for trial in range(256):
        rng = random.Random(33017125 + trial)
        transformed = [{source: values.copy() for source, values in page.items()} for page in pages]
        for page in transformed:
            rng.shuffle(page["line-runes"])
            rng.shuffle(page["word-runes"])
        scores = outputs(transformed, labels, model, floor)
        assert [name for name in plan["arms"] if scores[name]["score"] is not None] == eligible
        best = max(eligible, key=lambda name: scores[name]["score"])
        trials.append({"seed": 33017125 + trial, "arm_scores": {name: scores[name]["score"] for name in eligible},
                       "global_best": {"arm": best, "score": scores[best]["score"]}})
    best_arm = max(eligible, key=lambda name: observed[name]["score"])
    exceeded = sum(row["global_best"]["score"] >= observed[best_arm]["score"] for row in trials)
    return {"schema": "liberpedia-layout-count-streams-v1", "plan_sha256": sha(plan_bytes),
            "page_count": len(pages), "event_counts": {source: sum(len(page[source]) for page in pages) for source in SOURCE_IDS},
            "event_ranges": {source: [min(value for page in pages for value in page[source]),
                                      max(value for page in pages for value in page[source])] for source in SOURCE_IDS},
            "page_counts": pages, "observed": observed, "eligible_arms": eligible, "planted_controls": controls,
            "null_trials": trials, "observed_best": {"arm": best_arm, "score": observed[best_arm]["score"]},
            "null_at_or_above_observed": exceeded, "empirical_global_p": (exceeded + 1) / 257}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: eight count-stream arms, 256 matched full-grid shuffles, eight planted controls")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"best": result["observed_best"], "at_or_above": result["null_at_or_above_observed"]}))
