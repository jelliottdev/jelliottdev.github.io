"""Optional accelerated independent full-grid check (NumPy and Numba required).

Unlike run.py, this scores GP rune outputs by rolling numeric A-Z quadgram
states without constructing Latin strings. The stdlib check.py is the portable
fallback for readers without these optional libraries.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ALPHABET_SIZE = 26 ** 4


@njit
def score_one(cipher, key, offset, sign, symbols, sizes, frequencies):
    state = 0
    chars = 0
    total = 0.0
    for i in range(len(cipher)):
        symbol = (cipher[i] + sign * key[offset + i]) % 29
        for j in range(sizes[symbol]):
            state = (state * 26 + symbols[symbol, j]) % ALPHABET_SIZE
            chars += 1
            if chars >= 4:
                total += frequencies[state]
    return total / (chars - 3)


@njit
def search_pages(pages, lengths, key, symbols, sizes, frequencies):
    winners = np.empty((len(lengths), 3), dtype=np.float64)
    for p in range(len(lengths)):
        cipher = pages[p, :lengths[p]]
        best_score = -1e300
        best_offset = -1
        best_sign = 0
        for offset in range(len(key) - lengths[p] + 1):
            for sign in (-1, 1):
                value = score_one(cipher, key, offset, sign, symbols, sizes, frequencies)
                if value > best_score:
                    best_score = value
                    best_offset = offset
                    best_sign = sign
        winners[p, 0] = best_score
        winners[p, 1] = best_offset
        winners[p, 2] = best_sign
    return winners


def load():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == result["plan_sha256"]
    for entry in plan["inputs"]:
        assert hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]
    alpha = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {row["rune"]: i for i, row in enumerate(alpha)}
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, row in enumerate(alpha):
        sizes[i] = len(row["latin"])
        for j, letter in enumerate(row["latin"]):
            symbols[i, j] = ord(letter) - 65
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    norm = math.log10(sum(counts.values()))
    frequencies = np.full(ALPHABET_SIZE, math.log10(0.01) - norm, dtype=np.float64)
    for gram, amount in counts.items():
        state = 0
        for letter in gram:
            state = state * 26 + ord(letter) - 65
        frequencies[state] = math.log10(amount) - norm
    key_list = []
    for section in plan["sections"]:
        with (ROOT / section["path"]).open(encoding="utf-8", newline="") as file:
            key_list.extend(int(row["output_index"]) for row in csv.DictReader(file))
    key = np.array(key_list, dtype=np.int64)
    assert hashlib.sha256(bytes(key_list)).hexdigest() == result["source"]["indices_sha256"]
    page_lists = []
    for page in plan["targets"]:
        source = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        page_lists.append([lookup[rune] for rune in source if rune in lookup])
    lengths = np.array([len(row) for row in page_lists], dtype=np.int64)
    pages = np.zeros((len(lengths), max(lengths)), dtype=np.int64)
    for i, row in enumerate(page_lists):
        pages[i, :len(row)] = row
    return plan, result, pages, lengths, key, symbols, sizes, frequencies


def verify():
    plan, result, pages, lengths, key, symbols, sizes, frequencies = load()
    # Fixed cross-section against the portable producer, including non-winners.
    # The complete-grid check below remains a separate numeric implementation.
    from run import plaintext, quadgram_model, score
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    labels = [row["latin"] for row in alphabet]
    probabilities, floor = quadgram_model(ROOT / plan["model"])
    for page_index, offset, sign in ((0, 0, -1), (0, 330, 1), (14, 703, -1),
                                     (31, 1700, 1), (48, 2270, -1), (54, 2300, 1)):
        cipher = pages[page_index, :lengths[page_index]]
        expected = score(plaintext(cipher.tolist(), key.tolist(), offset, sign, labels),
                         probabilities, floor)
        actual = score_one(cipher, key, offset, sign, symbols, sizes, frequencies)
        assert math.isclose(actual, expected, rel_tol=0, abs_tol=1e-11)
    observed = search_pages(pages, lengths, key, symbols, sizes, frequencies)
    assert len(observed) == len(result["observed"])
    for actual, saved in zip(observed, result["observed"]):
        assert int(actual[1]) == saved["offset"] and int(actual[2]) == saved["sign"]
        assert math.isclose(actual[0], saved["score"], rel_tol=0, abs_tol=1e-11)
    assert math.isclose(max(observed[:, 0]), result["observed_global_best"]["score"], abs_tol=1e-11)
    for saved in result["null_global_maxima"]:
        values = key.tolist()
        random.Random(saved["seed"]).shuffle(values)
        assert hashlib.sha256(bytes(values)).hexdigest() == saved["key_sha256"]
        winners = search_pages(pages, lengths, np.array(values, dtype=np.int64), symbols, sizes, frequencies)
        index = int(np.argmax(winners[:, 0]))
        actual = winners[index]
        assert plan["targets"][index] == saved["page"]
        assert int(actual[1]) == saved["offset"] and int(actual[2]) == saved["sign"]
        assert math.isclose(actual[0], saved["score"], rel_tol=0, abs_tol=1e-11)
    print("PASS: distinct numeric quadgram engine independently searched every whole-page candidate")


if __name__ == "__main__":
    verify()
