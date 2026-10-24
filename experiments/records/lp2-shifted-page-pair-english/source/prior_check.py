"""Independent JSON-source and numeric rolling-quadgram replay of the full grid."""
from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
MOD = 26 ** 4


@njit
def one_stream(first, second, direction, letters, letter_count, table):
    accumulator = 0.0
    state = 0
    characters = 0
    for slot in range(min(len(first), len(second))):
        if direction == 0:
            rune = (first[slot] + second[slot]) % 29
        elif direction == 1:
            rune = (first[slot] - second[slot] + 29) % 29
        else:
            rune = (second[slot] - first[slot] + 29) % 29
        for col in range(letter_count[rune]):
            state = (state * 26 + letters[rune, col]) % MOD
            characters += 1
            if characters > 3:
                accumulator += table[state]
    groups = max(0, characters - 3)
    return accumulator / groups if groups >= 100 else -1e300, groups


@njit
def full_grid(rows, lengths, letters, letter_count, table):
    scores = np.empty((len(lengths) * (len(lengths) - 1) // 2, 3), np.float64)
    groups = np.empty_like(scores, dtype=np.int64)
    slot = 0
    for left in range(len(lengths)):
        for right in range(left + 1, len(lengths)):
            for direction in range(3):
                score, count = one_stream(rows[left, :lengths[left]], rows[right, :lengths[right]],
                                          direction, letters, letter_count, table)
                scores[slot, direction] = score
                groups[slot, direction] = count
            slot += 1
    return scores, groups


def setup():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    results = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(plan_bytes).hexdigest() == results["plan_sha256"]
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    alpha = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {entry["rune"]: position for position, entry in enumerate(alpha)}
    letters = np.zeros((29, 2), np.int64)
    counts = np.zeros(29, np.int64)
    for position, entry in enumerate(alpha):
        counts[position] = len(entry["latin"])
        for col, char in enumerate(entry["latin"]):
            letters[position, col] = ord(char) - ord("A")
    frequencies = {}
    for row in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = row.split()
        frequencies[gram] = int(count)
    mass = math.log10(sum(frequencies.values()))
    table = np.full(MOD, math.log10(0.01) - mass, np.float64)
    for gram, count in frequencies.items():
        idx = sum((ord(letter) - 65) * 26 ** (3 - n) for n, letter in enumerate(gram))
        table[idx] = math.log10(count) - mass
    values = []
    for page in plan["targets"]:
        document = json.loads((ROOT / f"data/pages/{page}.json").read_text(encoding="utf-8"))
        # Use structured physical line glyphs, not the text files read by the producer.
        values.append([lookup[ch] for line in document["lines"] for ch in line["raw"] if ch in lookup])
    lengths = np.asarray([len(row) for row in values], dtype=np.int64)
    assert len(values) == 55 and dict(zip(plan["targets"], lengths.tolist())) == results["page_lengths"]
    padded = np.zeros((55, int(max(lengths))), np.int64)
    for row, values_row in enumerate(values):
        padded[row, :len(values_row)] = values_row
    return plan, results, padded, lengths, letters, counts, table, alpha


def reshuffle(rows, lengths, seed):
    boundaries = sorted(set(int(length) for length in lengths))
    output = rows.copy()
    randomizer = random.Random(seed)
    for row, n in enumerate(lengths):
        begin = 0
        for end in boundaries:
            if end > n:
                break
            portion = output[row, begin:end].tolist()
            randomizer.shuffle(portion)
            output[row, begin:end] = portion
            begin = end
    return output


def verify():
    plan, saved, pages, lengths, letters, counts, table, alphabet = setup()
    pairs = [(i, j) for i in range(55) for j in range(i + 1, 55)]
    observed, groups = full_grid(pages, lengths, letters, counts, table)
    assert len(saved["observed_cases"]) == len(pairs) * 3 == 4455
    assert int(np.count_nonzero(groups >= 100)) == saved["eligible_cases"]
    for pair_position, (left, right) in enumerate(pairs):
        for arm in range(3):
            published = saved["observed_cases"][pair_position * 3 + arm]
            assert (published["page_a"], published["page_b"], published["operation"]) == (
                plan["targets"][left], plan["targets"][right], plan["operations"][arm])
            assert published["quadgrams"] == int(groups[pair_position, arm])
            actual = float(observed[pair_position, arm])
            if published["score"] is None:
                assert actual == -1e300
            else:
                assert math.isclose(actual, published["score"], rel_tol=0, abs_tol=1e-11)
    assert math.isclose(float(np.max(observed)), saved["observed_best"]["score"], abs_tol=1e-11)
    for stored in saved["null_global_maxima"]:
        randomized = reshuffle(pages, lengths, stored["seed"])
        grid, groups = full_grid(randomized, lengths, letters, counts, table)
        index = int(np.argmax(grid))
        pair_position, arm = divmod(index, 3)
        left, right = pairs[pair_position]
        assert (stored["page_a"], stored["page_b"], stored["operation"]) == (
            plan["targets"][left], plan["targets"][right], plan["operations"][arm])
        assert stored["eligible"] == int(np.count_nonzero(groups >= 100))
        assert math.isclose(stored["score"], float(grid[pair_position, arm]), rel_tol=0, abs_tol=1e-11)
    # A separate string scorer checks all three operations at two fixed observed pairs.
    counts_by_gram = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        counts_by_gram[gram] = int(count)
    normalizer = math.log10(sum(counts_by_gram.values()))
    for left, right in ((0, 1), (2, 18)):
        for arm in range(3):
            n = min(lengths[left], lengths[right])
            output = []
            for pos in range(n):
                a, b = int(pages[left, pos]), int(pages[right, pos])
                output.append((a + b) % 29 if arm == 0 else (a - b) % 29 if arm == 1 else (b - a) % 29)
            text = "".join(alphabet[index]["latin"] for index in output)
            values = [math.log10(counts_by_gram.get(text[pos:pos+4], 0.01)) - normalizer
                      for pos in range(len(text)-3)]
            direct = sum(values) / len(values) if len(values) >= 100 else -1e300
            numeric, _ = one_stream(pages[left, :lengths[left]], pages[right, :lengths[right]],
                                    arm, letters, counts, table)
            assert math.isclose(direct, numeric, rel_tol=0, abs_tol=1e-11)
    print("PASS: independent page-JSON source, all 4,455 scores and 256 whole-grid conditional controls")


if __name__ == "__main__":
    verify()
