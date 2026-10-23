"""Full-page LP2 search with archived decoded GP readings as a running key."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_plan() -> tuple[dict, bytes]:
    raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(raw)
    for entry in plan["inputs"]:
        path = ROOT / entry["path"]
        if digest(path.read_bytes()) != entry["sha256"]:
            raise ValueError(f"Input changed: {path}")
    return plan, raw


def reading_indices(path: Path) -> list[int]:
    with path.open(encoding="utf-8", newline="") as handle:
        values = [int(row["output_index"]) for row in csv.DictReader(handle)]
    if not values or any(v < 0 or v >= 29 for v in values):
        raise ValueError(f"Invalid reading trace: {path}")
    return values


def quadgram_model(path: Path) -> tuple[dict[str, float], float]:
    counts: dict[str, int] = {}
    for row in path.read_text(encoding="ascii").splitlines():
        gram, count = row.split()
        counts[gram] = int(count)
    total = sum(counts.values())
    log_total = math.log10(total)
    return {gram: math.log10(n) - log_total for gram, n in counts.items()}, math.log10(0.01) - log_total


def plaintext(cipher: list[int], key: list[int], offset: int, sign: int, labels: list[str]) -> str:
    return "".join(labels[(c + sign * key[offset + i]) % 29] for i, c in enumerate(cipher))


def score(text: str, probabilities: dict[str, float], floor: float) -> float:
    n = len(text) - 3
    return sum(probabilities.get(text[i:i + 4], floor) for i in range(n)) / n


def search_one(cipher: list[int], key: list[int], labels: list[str], probabilities: dict[str, float], floor: float) -> dict:
    best = (-math.inf, 0, -1, "")
    evaluations = 0
    for offset in range(len(key) - len(cipher) + 1):
        for sign in (-1, 1):
            text = plaintext(cipher, key, offset, sign, labels)
            value = score(text, probabilities, floor)
            evaluations += 1
            if value > best[0]:
                best = (value, offset, sign, text)
    value, offset, sign, text = best
    return {"score": value, "offset": offset, "sign": sign,
            "latin_sha256": digest(text.encode("ascii")), "latin_preview": text[:120],
            "evaluations": evaluations}


def report() -> dict:
    plan, plan_bytes = load_plan()
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    labels = [row["latin"] for row in alphabet]
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    sections = []
    key = []
    starts = {}
    for section in plan["sections"]:
        starts[section["id"]] = len(key)
        values = reading_indices(ROOT / section["path"])
        if len(values) != section["runes"]:
            raise ValueError(f"Reading length changed: {section['id']}")
        sections.append({"id": section["id"], "start": len(key), "runes": len(values)})
        key.extend(values)
    assert len(key) == 2892
    pages = {}
    for page in plan["targets"]:
        raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        pages[page] = [lookup[c] for c in raw if c in lookup]
        assert 66 <= len(pages[page]) <= 277
    probabilities, floor = quadgram_model(ROOT / plan["model"])

    plant_plain = reading_indices(ROOT / plan["plant"]["plaintext_path"])
    control_key = []
    control_starts = {}
    for section in plan["sections"]:
        if section["id"] == plan["plant"]["held_out_key_section"]:
            continue
        control_starts[section["id"]] = len(control_key)
        control_key.extend(reading_indices(ROOT / section["path"]))
    plant_offset = control_starts[plan["plant"]["key_section"]] + plan["plant"]["offset_in_section"]
    assert plant_offset + len(plant_plain) <= control_starts[plan["plant"]["key_section"]] + next(x["runes"] for x in sections if x["id"] == plan["plant"]["key_section"])
    plant_cipher = [(p + control_key[plant_offset + i]) % 29 for i, p in enumerate(plant_plain)]
    plant = search_one(plant_cipher, control_key, labels, probabilities, floor)
    recovered = [(c - control_key[plant_offset + i]) % 29 for i, c in enumerate(plant_cipher)]
    plant["exact_recovery"] = recovered == plant_plain
    plant["true_offset"] = plant_offset
    plant["true_sign"] = -1
    plant["held_out_key_section"] = plan["plant"]["held_out_key_section"]
    plant["control_key_runes"] = len(control_key)
    plant["true_score"] = score("".join(labels[p] for p in plant_plain), probabilities, floor)
    plant["top_recovers_true_offset"] = plant["offset"] == plant_offset and plant["sign"] == -1
    if not plant["exact_recovery"] or not plant["top_recovers_true_offset"]:
        raise ValueError("Planted complete-reading recovery failed; do not score LP2")

    observed = []
    for page, cipher in pages.items():
        observed.append({"page": page, "runes": len(cipher), **search_one(cipher, key, labels, probabilities, floor)})
    observed_best = max(observed, key=lambda row: row["score"])
    nulls = []
    for seed in plan["shuffle_seeds"]:
        shuffled = key.copy()
        random.Random(seed).shuffle(shuffled)
        best = None
        for page, cipher in pages.items():
            row = search_one(cipher, shuffled, labels, probabilities, floor)
            if best is None or row["score"] > best["score"]:
                best = {"page": page, "runes": len(cipher), **row}
        assert best is not None
        nulls.append({"seed": seed, "key_sha256": digest(bytes(shuffled)), **best})
    exceeded = sum(row["score"] >= observed_best["score"] for row in nulls)
    return {"schema": "liberpedia-solved-reading-running-key-v1",
            "plan_sha256": digest(plan_bytes), "source": {"sections": sections, "runes": len(key), "indices_sha256": digest(bytes(key))},
            "model": {"path": plan["model"], "quadgrams": len(probabilities), "floor": floor},
            "plant": plant, "observed": observed,
            "observed_global_best": observed_best,
            "null_global_maxima": nulls,
            "null_at_or_above_observed": exceeded,
            "empirical_global_p": (exceeded + 1) / (len(nulls) + 1),
            "total_observed_evaluations": sum(row["evaluations"] for row in observed)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: complete running-key grid and shared shuffled-key maxima")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"plant": result["plant"]["top_recovers_true_offset"],
                          "observed_best": result["observed_global_best"]["score"],
                          "null_at_or_above": result["null_at_or_above_observed"],
                          "evaluations": result["total_observed_evaluations"]}))
