"""Separate affine decoder and quadgram implementation for the full saved census."""
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
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
expected = {entry["path"]: entry["sha256"] for entry in plan["inputs"]}
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]


def pinned(path):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == expected[path.relative_to(ROOT).as_posix()]
    return data


alpha = json.loads(pinned(ROOT / "data/index.json"))["alphabet"]
ordinal = {entry["rune"]: index for index, entry in enumerate(alpha)}
latin = tuple(entry["latin"] for entry in alpha)
model_rows = [line.split() for line in pinned(ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
denominator = sum(int(amount) for _, amount in model_rows)
floor = math.log10(0.01 / denominator)
quadgrams = {gram: math.log10(int(n) / denominator) for gram, n in model_rows}
codepoints = np.full(26 ** 4, floor, dtype=np.float64)
for gram, value in quadgrams.items():
    address = 0
    for letter in gram:
        address = 26 * address + (ord(letter) - 65)
    codepoints[address] = value
letters = np.zeros((29, 2), dtype=np.int64)
widths = np.zeros(29, dtype=np.int64)
for index, spelling in enumerate(latin):
    widths[index] = len(spelling)
    for j, letter in enumerate(spelling):
        letters[index, j] = ord(letter) - 65


@njit
def score_affine(cipher, a, b, letters, widths, codepoints):
    # Unlike the producer's rolling-state kernel, materialize the entire
    # decoded letter string, then enumerate its four-character windows.
    text = np.empty(len(cipher) * 2, dtype=np.int64)
    used = 0
    for rune in cipher:
        decoded = (a * rune + b) % 29
        for j in range(widths[decoded]):
            text[used] = letters[decoded, j]
            used += 1
    total = 0.0
    for start in range(used - 3):
        slot = ((text[start] * 26 + text[start + 1]) * 26 + text[start + 2]) * 26 + text[start + 3]
        total += codepoints[slot]
    return total / (used - 3)


@njit
def check_grid(pages, lengths, letters, widths, codepoints):
    matrix = np.empty((len(lengths), 812), dtype=np.float64)
    for page in range(len(lengths)):
        text = pages[page, :lengths[page]]
        for a in range(1, 29):
            for b in range(29):
                matrix[page, (a - 1) * 29 + b] = score_affine(text, a, b, letters, widths, codepoints)
    return matrix


streams = []
for page_id in plan["pages"]:
    page = json.loads(pinned(ROOT / f"data/pages/{page_id}.json"))
    runes = tuple(ordinal[r] for r in page["raw"] if r in ordinal)
    assert len(runes) == page["rune_count"] and len(runes) >= 66
    streams.append(runes)
assert json.loads(pinned(ROOT / "data/pages/lp2-50.json"))["rune_count"] == 0
assert len(streams) == saved["page_count"] == 55
lengths = np.array(list(map(len, streams)), dtype=np.int64)
pages = np.zeros((len(streams), int(max(lengths))), dtype=np.int64)
for i, values in enumerate(streams):
    pages[i, :len(values)] = values
matrix = check_grid(pages, lengths, letters, widths, codepoints)
assert matrix.shape == (55, 812)
case_data = (HERE / "cases.jsonl").read_bytes()
assert hashlib.sha256(case_data).hexdigest() == saved["cases_sha256"]
cases = [json.loads(line) for line in case_data.splitlines()]
assert len(cases) == saved["case_count"] == 44660
for page_index, (page_id, cipher) in enumerate(zip(plan["pages"], streams)):
    for a in range(1, 29):
        for b in range(29):
            entry = cases[page_index * 812 + (a - 1) * 29 + b]
            assert (entry["page"], entry["a"], entry["b"]) == (page_id, a, b)
            assert math.isclose(entry["score"], matrix[page_index, (a - 1) * 29 + b], abs_tol=1e-11)
            output = bytes((a * rune + b) % 29 for rune in cipher)
            assert hashlib.sha256(output).hexdigest() == entry["output_sha256"]
winner = max(cases, key=lambda row: (row["score"], -int(row["page"][4:]), -row["a"], -row["b"]))
assert winner == saved["best_case"]
assert int(np.count_nonzero(matrix >= plan["score_threshold"])) == saved["threshold_passes"]


def portable_score(indices):
    plain = "".join(latin[i] for i in indices)
    return sum(quadgrams.get(plain[pos:pos + 4], floor) for pos in range(len(plain) - 3)) / (len(plain) - 3)


genuine = 0
plants = 0
a, b = plan["positive_control_map"].values()
inverse = pow(a, -1, 29)
for index, row in enumerate(saved["control_gate"]["rows"]):
    source = pinned(ROOT / f"exports/readings/{row['reading']}.csv").decode("utf-8-sig")
    clear = tuple(int(entry["output_index"]) for entry in csv.DictReader(source.splitlines()))
    assert len(clear) == row["runes"]
    assert math.isclose(portable_score(clear), row["source_score"], abs_tol=1e-11)
    better = 0
    for rep in range(plan["control_replicates"]):
        mixed = list(clear)
        random.Random(plan["control_seed"] + 1000 * index + rep).shuffle(mixed)
        better += portable_score(mixed) < row["source_score"]
    assert better == row["shuffles_below"]
    genuine += row["source_score"] >= plan["score_threshold"] and better >= 198
    coded = np.array([inverse * (symbol - b) % 29 for symbol in clear], dtype=np.int64)
    scores = sorted(((score_affine(coded, x, y, letters, widths, codepoints), x, y)
                     for x in range(1, 29) for y in range(29)),
                    key=lambda record: (-record[0], record[1], record[2]))
    rank = next(position + 1 for position, rec in enumerate(scores) if rec[1:] == (a, b))
    assert rank == row["planted_true_rank"]
    plants += rank == 1
assert genuine == saved["control_gate"]["good_originals"] == 9
assert plants == saved["control_gate"]["top_rank_plants"] == 9
assert saved["control_gate"]["passed"]

nulls = []
for rep in range(plan["null_replicates"]):
    mixed = np.zeros_like(pages)
    for index, original in enumerate(streams):
        shuffled = list(original)
        random.Random(plan["null_seed"] + 1000 * rep + index).shuffle(shuffled)
        mixed[index, :len(shuffled)] = shuffled
    nulls.append(float(np.max(check_grid(mixed, lengths, letters, widths, codepoints))))
assert len(nulls) == len(saved["null_maxima"]) == 199
assert all(math.isclose(a, b, abs_tol=1e-11) for a, b in zip(nulls, saved["null_maxima"]))
above = sum(value >= winner["score"] for value in nulls)
assert above == saved["null_at_least_best"]
assert math.isclose((1 + above) / 200, saved["empirical_global_tail"], abs_tol=1e-12)
print("PASS: independent 44,660-case affine census, solved controls and 199 full-search nulls")
