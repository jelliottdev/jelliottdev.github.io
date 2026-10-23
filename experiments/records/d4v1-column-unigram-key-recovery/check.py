"""Independent histogram-based key inference and assembled-text score check."""
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
SAVED = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
PIN = {item["path"]: item["sha256"] for item in PLAN["inputs"]}


def read(name):
    data = (ROOT / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == PIN[name], name
    return data


@njit
def key_by_histogram(cipher, excluded, period, target):
    frequencies = np.zeros((period, 29), dtype=np.int64)
    clean_position = 0
    for original in range(len(cipher)):
        if not excluded[original]:
            frequencies[clean_position % period, cipher[original]] += 1
            clean_position += 1
    answer = np.zeros(period, dtype=np.int64)
    for column in range(period):
        highest = -1.0
        for shift in range(29):
            score = 0.0
            size = 0
            for rune in range(29):
                size += frequencies[column, rune]
            for decoded in range(29):
                cipher_rune = (decoded + shift) % 29
                score += (frequencies[column, cipher_rune] / size) * target[decoded]
            if score > highest:
                highest = score
                answer[column] = shift
    return answer


@njit
def score_assembled(cipher, key, sizes, symbols, weights):
    letters = np.empty(len(cipher) * 2, dtype=np.int64)
    used = 0
    for i in range(len(cipher)):
        rune = (cipher[i] - key[i % len(key)] + 29) % 29
        for j in range(sizes[rune]):
            letters[used] = symbols[rune, j]
            used += 1
    total = 0.0
    for i in range(used - 3):
        slot = ((letters[i] * 26 + letters[i + 1]) * 26 + letters[i + 2]) * 26 + letters[i + 3]
        total += weights[slot]
    return total / (used - 3)


def main():
    assert SAVED["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    alphabet = json.loads(read("data/index.json"))["alphabet"]
    index = {row["rune"]: i for i, row in enumerate(alphabet)}
    sizes = np.array([len(row["latin"]) for row in alphabet], dtype=np.int64)
    symbols = np.zeros((29, 2), dtype=np.int64)
    for i, row in enumerate(alphabet):
        for j, ch in enumerate(row["latin"]):
            symbols[i, j] = ord(ch) - 65
    model = [line.split() for line in read("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
    scale = sum(int(n) for _, n in model)
    weights = np.full(26 ** 4, math.log10(.01 / scale), dtype=np.float64)
    for gram, amount in model:
        key = 0
        for ch in gram:
            key = key * 26 + ord(ch) - 65
        weights[key] = math.log10(int(amount) / scale)
    target = np.array(json.loads(read("experiments/records/d4v1-column-unigram-key-recovery/source-target.json"))["known_page_unigram_target"], dtype=np.float64)
    interrupted = json.loads(read("experiments/records/d4v1-column-unigram-key-recovery/interrupt-map.json"))["pages"]
    pages = []
    for name in PLAN["pages"]:
        data = json.loads(read(f"data/pages/{name}.json"))
        cipher = np.array([index[ch] for ch in data["raw"] if ch in index], dtype=np.int64)
        assert len(cipher) == data["rune_count"]
        omitted = np.zeros(len(cipher), dtype=np.bool_)
        for offset in interrupted[name]["positions"]:
            if offset < len(cipher):
                omitted[offset] = True
        pages.append((name, cipher, omitted))
    lookup = {(row["page"], row["period"]): row for row in SAVED["rows"]}
    assert len(lookup) == 165
    best = None
    for name, cipher, omit in pages:
        for period in PLAN["fixed_periods"]:
            key = key_by_histogram(cipher, omit, period, target)
            found = lookup[name, period]
            assert list(key) == found["key"], (name, period)
            score = float(score_assembled(cipher, key, sizes, symbols, weights))
            assert abs(score - found["score"]) < 1e-11, (name, period)
            if best is None or score > best["score"]:
                best = found
    assert best == SAVED["best"]
    # Confirm every page-specific positive, including failures, under an
    # independently assembled known-reading plaintext.
    passage = [int(row["output_index"]) for row in csv.DictReader(read("exports/readings/welcome.csv").decode("utf-8-sig").splitlines())]
    plant_rows = {(row["page"], row["period"]): row for row in SAVED["page_plants"]}
    for name, cipher, omitted in pages:
        message = np.array([passage[i % len(passage)] for i in range(len(cipher))], dtype=np.int64)
        for period in PLAN["fixed_periods"]:
            planted_key = np.array([(j * j + 3 * j + 1) % 29 for j in range(period)], dtype=np.int64)
            synthetic = (message + np.resize(planted_key, len(message))) % 29
            inferred = key_by_histogram(synthetic, omitted, period, target)
            stored = plant_rows[name, period]
            assert list(inferred) == stored["inferred_key"]
            assert bool(np.array_equal(inferred, planted_key)) == stored["exact_key_recovery"]
            text_score = float(score_assembled(message, np.zeros(1, dtype=np.int64), sizes, symbols, weights))
            assert abs(text_score - stored["known_text_english_score"]) < 1e-11
            assert text_score >= PLAN["score_threshold"]
            assert stored["exact_key_recovery"] == lookup[name, period]["powered_by_page_plant"]
    maxima = []
    for rep in range(199):
        largest = -1e10
        for page_index, (_name, cipher, omitted) in enumerate(pages):
            shuffled = [int(n) for n in cipher]
            random.Random(3301 + 10000 * rep + page_index).shuffle(shuffled)
            values = np.array(shuffled, dtype=np.int64)
            for period in PLAN["fixed_periods"]:
                key = key_by_histogram(values, omitted, period, target)
                largest = max(largest, float(score_assembled(values, key, sizes, symbols, weights)))
        maxima.append(largest)
    assert np.allclose(maxima, SAVED["null_maxima"], atol=1e-11, rtol=0)
    assert sum(x >= best["score"] for x in maxima) == SAVED["null_at_least_actual"]
    parity = json.loads((HERE / "source-parity.json").read_text(encoding="utf-8"))
    for case in parity["cases"]:
        assert lookup[case["site_page"], case["period"]]["key"] == case["key"]
    print("Independent histogram inference, 165 outcomes, 165 plants and 199 complete-search nulls pass")


if __name__ == "__main__":
    main()
