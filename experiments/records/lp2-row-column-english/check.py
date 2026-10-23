"""Independent page-JSON route reconstruction and complete-score replay."""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RADIX = 26 ** 4


@njit
def score_single(source, permutation, count, glyphs, sizes, weights):
    window = 0
    characters = 0
    total = 0.0
    for offset in range(count):
        symbol = source[permutation[offset]]
        for index in range(sizes[symbol]):
            window = (window * 26 + glyphs[symbol, index]) % RADIX
            characters += 1
            if characters > 3:
                total += weights[window]
    n = max(0, characters - 3)
    return total/n if n >= 100 else -1e300, n


@njit
def all_scores(corpus, owners, orders, lengths, glyphs, sizes, weights):
    results = np.empty(len(owners), np.float64)
    counts = np.empty(len(owners), np.int64)
    for case in range(len(owners)):
        score, count = score_single(corpus[owners[case]], orders[case], lengths[case], glyphs, sizes, weights)
        results[case], counts[case] = score, count
    return results, counts


def reconstruct(rows, axis, outer, reverse, alternating):
    total_groups = len(rows) if axis == "row" else max(map(len, rows))
    groups = list(range(total_groups))
    if outer:
        groups = list(reversed(groups))
    coordinates = []
    for visit, group_no in enumerate(groups):
        if axis == "row":
            chunk = [(group_no, col) for col in range(len(rows[group_no]))]
        else:
            chunk = [(row, group_no) for row in range(len(rows)) if group_no < len(rows[row])]
        if reverse != (alternating and visit % 2 == 1):
            chunk.reverse()
        coordinates.extend(chunk)
    starts = []
    accumulated = 0
    for row in rows:
        starts.append(accumulated)
        accumulated += len(row)
    return [starts[row] + col for row, col in coordinates]


def load():
    plan_bytes = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_bytes)
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(plan_bytes).hexdigest() == result["plan_sha256"]
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    rune_index = {entry["rune"]: n for n, entry in enumerate(alphabet)}
    glyphs = np.zeros((29, 2), np.int64)
    sizes = np.zeros(29, np.int64)
    for n, entry in enumerate(alphabet):
        sizes[n] = len(entry["latin"])
        for col, ch in enumerate(entry["latin"]):
            glyphs[n, col] = ord(ch) - ord("A")
    frequencies = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        frequencies[gram] = int(amount)
    divisor = math.log10(sum(frequencies.values()))
    weights = np.full(RADIX, math.log10(.01) - divisor, np.float64)
    for gram, amount in frequencies.items():
        slot = sum((ord(ch) - 65) * 26 ** (3 - col) for col, ch in enumerate(gram))
        weights[slot] = math.log10(amount) - divisor
    archive = json.loads((ROOT / "experiments/records/lp2-row-column-routes/results.json").read_text(encoding="utf-8"))
    archive_by_id = {page["page"]: page for page in archive["pages"]}
    values = []
    metadata = []
    orders = []
    owners = []
    for page_id in plan["targets"]:
        raw = json.loads((ROOT / f"data/pages/{page_id}.json").read_text(encoding="utf-8"))
        rows = [[rune_index[ch] for ch in line["raw"] if ch in rune_index] for line in raw["lines"]]
        rows = [row for row in rows if row]
        source = [symbol for row in rows for symbol in row]
        assert source == [item["index"] for item in archive_by_id[page_id]["source_positions"]]
        assert len(source) == result["page_lengths"][page_id]
        owner = len(values)
        values.append(source)
        for axis, outer, reverse, alternating in itertools.product(("row", "column"), (False, True),
                                                                     (False, True), (False, True)):
            path = reconstruct(rows, axis, outer, reverse, alternating)
            assert sorted(path) == list(range(len(source)))
            archive_case = next(case for case in archive_by_id[page_id]["cases"]
                                if (case["axis"],case["outer_reverse"],case["inner_reverse"],case["alternating"])
                                == (axis,outer,reverse,alternating))
            assert path == archive_case["source_ordinals"]
            owners.append(owner)
            orders.append(path)
            metadata.append((page_id, axis, outer, reverse, alternating))
    assert len(owners) == 880
    source_matrix = np.zeros((55, max(map(len,values))), np.int64)
    for n, row in enumerate(values):
        source_matrix[n, :len(row)] = row
    order_matrix = np.zeros((880, source_matrix.shape[1]), np.int64)
    for n, order in enumerate(orders):
        order_matrix[n, :len(order)] = order
    lengths = np.asarray([len(path) for path in orders], np.int64)
    return plan, result, source_matrix, np.asarray([len(row) for row in values], np.int64), np.asarray(owners,np.int64), order_matrix, lengths, metadata, glyphs, sizes, weights, alphabet


def shuffle(corpus, lengths, seed):
    randomizer = random.Random(seed)
    copy = corpus.copy()
    for row, length in enumerate(lengths):
        values = copy[row, :length].tolist()
        randomizer.shuffle(values)
        copy[row, :length] = values
    return copy


def verify():
    (plan, result, pages, page_lengths, owners, orders, lengths, metadata,
     glyphs, sizes, weights, alphabet) = load()
    observed, groups = all_scores(pages, owners, orders, lengths, glyphs, sizes, weights)
    assert int(np.count_nonzero(groups >= 100)) == result["eligible_routes"]
    for n, stored in enumerate(result["observed_cases"]):
        assert metadata[n] == tuple(stored[key] for key in ("page","axis","outer_reverse","inner_reverse","alternating"))
        assert int(groups[n]) == stored["quadgrams"]
        if stored["score"] is None:
            assert observed[n] == -1e300
        else:
            assert math.isclose(observed[n], stored["score"], rel_tol=0, abs_tol=1e-11)
    winner = int(np.argmax(observed))
    assert metadata[winner] == tuple(result["observed_best"][key] for key in ("page","axis","outer_reverse","inner_reverse","alternating"))
    assert math.isclose(observed[winner], result["observed_best"]["score"], abs_tol=1e-11)
    for trial in result["null_global_maxima"]:
        randomized = shuffle(pages, page_lengths, trial["seed"])
        scores, group_counts = all_scores(randomized, owners, orders, lengths, glyphs, sizes, weights)
        index = int(np.argmax(scores))
        assert metadata[index] == tuple(trial[key] for key in ("page","axis","outer_reverse","inner_reverse","alternating"))
        assert int(np.count_nonzero(group_counts >= 100)) == trial["eligible_cases"]
        assert math.isclose(scores[index], trial["score"], rel_tol=0, abs_tol=1e-11)
    # Independent literal-string spot checks (winner and two nonwinning routes).
    probabilities = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        probabilities[gram] = int(count)
    norm = math.log10(sum(probabilities.values()))
    for case in (0, winner, 879):
        text = "".join(alphabet[int(pages[owners[case], ord])]["latin"] for ord in orders[case, :lengths[case]])
        if len(text) - 3 >= 100:
            direct = sum(math.log10(probabilities.get(text[i:i+4], .01)) - norm for i in range(len(text)-3)) / (len(text)-3)
            assert math.isclose(direct, observed[case], rel_tol=0, abs_tol=1e-11)
    assert reconstruct([list("ABC"),list("DE"),list("F")], "column",False,False,False) == [0,3,5,1,4,2]
    assert reconstruct([list("ABC"),list("DE"),list("F")], "row",False,False,True) == [0,1,2,4,3,5]
    print("PASS: independently rebuilt 880 route orders and all 256 full-route control searches")


if __name__ == "__main__":
    verify()
