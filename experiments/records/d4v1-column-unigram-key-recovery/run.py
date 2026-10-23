"""Fixed-KL replay of the pinned source's column-unigram key inference."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
PIN = {item["path"]: item["sha256"] for item in PLAN["inputs"]}


def pinned(name):
    data = (ROOT / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == PIN[name], name
    return data


@njit
def source_key(cipher, omit, period, target):
    # Source removes indexed runes only while solving columns. Its final preview
    # applies the resulting key to the original, unfiltered page.
    clean = np.empty(len(cipher), dtype=np.int64)
    used = 0
    for i in range(len(cipher)):
        if not omit[i]:
            clean[used] = cipher[i]
            used += 1
    key = np.empty(period, dtype=np.int64)
    for column in range(period):
        best_shift = 0
        best_fit = -1.0
        for shift in range(29):
            frequencies = np.zeros(29, dtype=np.float64)
            size = 0
            for i in range(column, used, period):
                frequencies[(clean[i] - shift + 29) % 29] += 1.0
                size += 1
            fit = 0.0
            if size:
                for rune in range(29):
                    fit += (frequencies[rune] / size) * target[rune]
            else:
                fit = -1.0
            if fit > best_fit:
                best_fit = fit
                best_shift = shift
        key[column] = best_shift
    return key


@njit
def english_score(cipher, key, letters, sizes, weights):
    state = 0
    count = 0
    total = 0.0
    for i in range(len(cipher)):
        value = (cipher[i] - key[i % len(key)] + 29) % 29
        for j in range(sizes[value]):
            state = (state * 26 + letters[value, j]) % (26 ** 4)
            count += 1
            if count >= 4:
                total += weights[state]
    return total / (count - 3)


def setup():
    alphabet = json.loads(pinned("data/index.json"))["alphabet"]
    lookup = {a["rune"]: i for i, a in enumerate(alphabet)}
    letters = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, a in enumerate(alphabet):
        sizes[i] = len(a["latin"])
        for j, ch in enumerate(a["latin"]):
            letters[i, j] = ord(ch) - 65
    model = [line.split() for line in pinned("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
    norm = sum(int(n) for _, n in model)
    weights = np.full(26 ** 4, math.log10(.01 / norm), dtype=np.float64)
    for gram, amount in model:
        slot = 0
        for ch in gram:
            slot = slot * 26 + ord(ch) - 65
        weights[slot] = math.log10(int(amount) / norm)
    source = json.loads(pinned("experiments/records/d4v1-column-unigram-key-recovery/source-target.json"))
    target = np.array(source["known_page_unigram_target"], dtype=np.float64)
    interrupts = json.loads(pinned("experiments/records/d4v1-column-unigram-key-recovery/interrupt-map.json"))["pages"]
    pages = []
    for name in PLAN["pages"]:
        data = json.loads(pinned(f"data/pages/{name}.json"))
        values = np.array([lookup[ch] for ch in data["raw"] if ch in lookup], dtype=np.int64)
        assert len(values) == data["rune_count"] and len(values) >= 66
        omitted = np.zeros(len(values), dtype=np.bool_)
        for position in interrupts[name]["positions"]:
            if position < len(values):
                omitted[position] = True
        pages.append((name, values, omitted))
    assert json.loads(pinned("data/pages/lp2-50.json"))["rune_count"] == 0
    return letters, sizes, weights, target, pages


def known_readings(letters, sizes, weights, target):
    rows = []
    for name in PLAN["readings"]:
        body = pinned(f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = np.array([int(row["output_index"]) for row in csv.DictReader(body.splitlines())], dtype=np.int64)
        score = float(english_score(plain, np.zeros(1, dtype=np.int64), letters, sizes, weights))
        recovered = {}
        for period in PLAN["fixed_periods"]:
            key = np.array([(i * i + 3 * i + 1) % 29 for i in range(period)], dtype=np.int64)
            cipher = (plain + np.resize(key, len(plain))) % 29
            inferred = source_key(cipher, np.zeros(len(cipher), dtype=np.bool_), period, target)
            recovered[str(period)] = bool(np.array_equal(key, inferred))
        rows.append({"reading": name, "runes": len(plain), "english_score": score,
                     "exact_key_recovery": recovered})
    return rows


def page_plants(pages, target, letters, sizes, weights):
    body = pinned("exports/readings/welcome.csv").decode("utf-8-sig")
    plain = [int(row["output_index"]) for row in csv.DictReader(body.splitlines())]
    rows = []
    for name, original, omit in pages:
        planted = np.array([plain[i % len(plain)] for i in range(len(original))], dtype=np.int64)
        english_score_of_plant = float(english_score(planted, np.zeros(1, dtype=np.int64), letters, sizes, weights))
        for period in PLAN["fixed_periods"]:
            key = np.array([(i * i + 3 * i + 1) % 29 for i in range(period)], dtype=np.int64)
            cipher = (planted + np.resize(key, len(planted))) % 29
            inferred = source_key(cipher, omit, period, target)
            rows.append({"page": name, "period": period, "runes": len(original),
                         "source_omitted_runes": int(np.sum(omit)),
                         "known_text_english_score": english_score_of_plant,
                         "exact_key_recovery": bool(np.array_equal(inferred, key)),
                         "inferred_key": [int(x) for x in inferred]})
    return rows


def source_auto_period(cipher):
    best_period, best_ioc = 1, 0.0
    for period in range(2, min(101, len(cipher) // 2)):
        sum_ioc = 0.0
        for column in range(period):
            values = cipher[column::period]
            if len(values) <= 1:
                continue
            counts = np.bincount(values, minlength=29)
            sum_ioc += sum(int(n) * (int(n) - 1) for n in counts) / (len(values) * (len(values) - 1))
        ioc = sum_ioc / period
        if ioc > best_ioc:
            best_period, best_ioc = period, ioc
    return best_period


def produce():
    letters, sizes, weights, target, pages = setup()
    known = known_readings(letters, sizes, weights, target)
    planted = page_plants(pages, target, letters, sizes, weights)
    counts = {str(p): sum(x["exact_key_recovery"][str(p)] for x in known) for p in PLAN["fixed_periods"]}
    assert all(x >= 8 for x in counts.values())
    assert sum(x["english_score"] >= PLAN["score_threshold"] for x in known) >= 8
    assert all(x["known_text_english_score"] >= PLAN["score_threshold"] for x in planted)
    # A pretarget calibration restricts negative interpretation to source contexts
    # where the page-length plant actually survives source key inference.
    auto = []
    for name in PLAN["readings"]:
        body = pinned(f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = np.array([int(row["output_index"]) for row in csv.DictReader(body.splitlines())], dtype=np.int64)
        key = np.array([1, 5, 11], dtype=np.int64)
        cipher = (plain + np.resize(key, len(plain))) % 29
        auto.append({"reading": name, "planted_period": 3, "source_auto_period": source_auto_period(cipher)})
    rows = []
    for name, stream, omit in pages:
        for period in PLAN["fixed_periods"]:
            key = source_key(stream, omit, period, target)
            score = float(english_score(stream, key, letters, sizes, weights))
            rows.append({"page": name, "period": period, "key": [int(x) for x in key],
                         "score": score,
                         "powered_by_page_plant": next(x["exact_key_recovery"] for x in planted
                                                      if x["page"] == name and x["period"] == period)})
    global_best = max(rows, key=lambda x: x["score"])
    null_maxima = []
    for rep in range(PLAN["control_replicates"]):
        highest = -1e10
        for i, (_name, stream, omit) in enumerate(pages):
            shuffled = [int(x) for x in stream]
            random.Random(PLAN["seed"] + 10000 * rep + i).shuffle(shuffled)
            cipher = np.array(shuffled, dtype=np.int64)
            for period in PLAN["fixed_periods"]:
                key = source_key(cipher, omit, period, target)
                highest = max(highest, float(english_score(cipher, key, letters, sizes, weights)))
        null_maxima.append(highest)
    exceed = sum(x >= global_best["score"] for x in null_maxima)
    return {"schema": "liberpedia-d4v1-column-unigram-results-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "known_readings": known, "known_recovery_count": counts,
            "page_plants": planted, "source_auto_period_controls": auto,
            "rows": rows, "best": global_best, "null_maxima": null_maxima,
            "null_at_least_actual": exceed,
            "selection_tail_plus_one": (exceed + 1) / (len(null_maxima) + 1),
            "powered_rows": sum(x["powered_by_page_plant"] for x in rows),
            "english_line_hits_all": sum(x["score"] >= PLAN["score_threshold"] for x in rows),
            "english_line_hits_powered": sum(x["powered_by_page_plant"] and x["score"] >= PLAN["score_threshold"] for x in rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.controls:
        letters, sizes, weights, target, pages = setup()
        known = known_readings(letters, sizes, weights, target)
        planted = page_plants(pages, target, letters, sizes, weights)
        print(json.dumps({"known_key_recovery": {str(p): sum(x["exact_key_recovery"][str(p)] for x in known) for p in PLAN["fixed_periods"]},
                          "page_plant_recovery": {str(p): sum(x["exact_key_recovery"] for x in planted if x["period"] == p) for p in PLAN["fixed_periods"]},
                          "powered_rows": sum(x["exact_key_recovery"] for x in planted)}))
    else:
        result = produce()
        file = HERE / "results.json"
        if args.check:
            assert result == json.loads(file.read_text(encoding="utf-8"))
            print("Complete source-column cohort, plants and full-selection nulls match")
        else:
            file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            print("Saved", len(result["rows"]), "page-period rows")
