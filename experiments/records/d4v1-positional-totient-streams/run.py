"""Bounded whole-page screen of one pinned positional-totient transform."""
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
INPUTS = {row["path"]: row["sha256"] for row in PLAN["inputs"]}
QUADS = 26**4


def read_pinned(name):
    blob = (ROOT / name).read_bytes()
    if hashlib.sha256(blob).hexdigest() != INPUTS[name]:
        raise ValueError(f"Changed input: {name}")
    return blob


def phi(n):
    if n <= 0:
        return 0
    value, factor, remaining = n, 2, n
    while factor * factor <= remaining:
        if remaining % factor == 0:
            while remaining % factor == 0:
                remaining //= factor
            value -= value // factor
        factor += 1
    if remaining > 1:
        value -= value // remaining
    return value


def setup():
    alphabet = json.loads(read_pinned("data/index.json"))["alphabet"]
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    labels = [row["latin"] for row in alphabet]
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, label in enumerate(labels):
        sizes[i] = len(label)
        for j, ch in enumerate(label):
            symbols[i, j] = ord(ch) - 65
    model = [line.split() for line in read_pinned("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
    total = sum(int(count) for _, count in model)
    floor = math.log10(0.01 / total)
    weights = np.full(QUADS, floor, dtype=np.float64)
    sparse = {}
    for gram, count in model:
        value = math.log10(int(count) / total)
        sparse[gram] = value
        state = 0
        for ch in gram:
            state = state * 26 + ord(ch) - 65
        weights[state] = value

    def portable(indices):
        text = "".join(labels[i] for i in indices)
        return sum(sparse.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)

    return lookup, labels, symbols, sizes, weights, portable


@njit
def numeric_score(cipher, shifts, symbols, sizes, weights):
    state = 0
    chars = 0
    amount = 0.0
    for position in range(len(cipher)):
        value = (cipher[position] - shifts[position] + 29) % 29
        for j in range(sizes[value]):
            state = (state * 26 + symbols[value, j]) % QUADS
            chars += 1
            if chars >= 4:
                amount += weights[state]
    return amount / (chars - 3)


@njit
def all_scores(pages, lengths, shifts, symbols, sizes, weights):
    scores = np.empty((len(lengths), len(shifts)), dtype=np.float64)
    for page in range(len(lengths)):
        cipher = pages[page, :lengths[page]]
        for offset in range(len(shifts)):
            scores[page, offset] = numeric_score(cipher, shifts[offset], symbols, sizes, weights)
    return scores


def page_data(lookup):
    streams = []
    for name in PLAN["pages"]:
        page = json.loads(read_pinned(f"data/pages/{name}.json"))
        values = [lookup[ch] for line in page["lines"] for ch in line["raw"] if ch in lookup]
        if len(values) != page["rune_count"] or len(values) < 66:
            raise ValueError(f"Rune count disagrees: {name}")
        streams.append(values)
    if json.loads(read_pinned("data/pages/lp2-50.json"))["rune_count"] != 0:
        raise ValueError("The excluded number-only page now has runes")
    lengths = np.array([len(x) for x in streams], dtype=np.int64)
    pages = np.zeros((len(streams), max(lengths)), dtype=np.int64)
    for i, row in enumerate(streams):
        pages[i, :len(row)] = row
    return streams, pages, lengths


def controls(portable):
    rows = []
    offset = PLAN["positive_control_offset"]
    for number, name in enumerate(PLAN["readings"]):
        body = read_pinned(f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = [int(row["output_index"]) for row in csv.DictReader(body.splitlines())]
        if len(plain) < 66:
            raise ValueError(f"Short known reading: {name}")
        direct = portable(plain)
        shuffled_below = 0
        for rep in range(PLAN["control_replicates"]):
            copy = plain.copy()
            random.Random(PLAN["control_seed"] + 1000 * number + rep).shuffle(copy)
            shuffled_below += portable(copy) < direct
        cipher = [(value + phi(i + offset)) % 29 for i, value in enumerate(plain)]
        ranked = sorted(
            ((portable([(value - phi(i + trial)) % 29 for i, value in enumerate(cipher)]), trial)
             for trial in range(PLAN["operator_count"])),
            key=lambda row: (-row[0], row[1]),
        )
        if [(value - phi(i + offset)) % 29 for i, value in enumerate(cipher)] != plain:
            raise ValueError("Planted text was not recovered")
        true_rank = next(i + 1 for i, row in enumerate(ranked) if row[1] == offset)
        rows.append({"reading": name, "runes": len(plain), "direct_score": direct,
                     "own_shuffles_below": shuffled_below, "planted_true_offset_rank": true_rank})
    recognized = sum(row["direct_score"] >= PLAN["score_threshold"] and row["own_shuffles_below"] >= 198 for row in rows)
    recovered = sum(row["planted_true_offset_rank"] == 1 for row in rows)
    return {"rows": rows, "recognized_readings": recognized, "top_rank_plants": recovered,
            "passed": recognized >= 8 and recovered >= 8}


def produce(control_only=False):
    lookup, labels, symbols, sizes, weights, portable = setup()
    gate = controls(portable)
    if not gate["passed"]:
        raise ValueError("Predetermined positive-control gate failed")
    if control_only:
        return {"controls": gate}
    streams, pages, lengths = page_data(lookup)
    shifts = np.zeros((PLAN["operator_count"], max(lengths)), dtype=np.int64)
    for offset in range(PLAN["operator_count"]):
        for i in range(max(lengths)):
            shifts[offset, i] = phi(i + offset) % 29
    measured = all_scores(pages, lengths, shifts, symbols, sizes, weights)
    page_rows = []
    for i, name in enumerate(PLAN["pages"]):
        offset = int(np.argmax(measured[i]))
        decoded = [(v - int(shifts[offset, j])) % 29 for j, v in enumerate(streams[i])]
        page_rows.append({"page": name, "runes": len(streams[i]), "best_offset": offset,
                          "best_score": float(measured[i, offset]),
                          "best_latin": "".join(labels[v] for v in decoded)})
    winner_index = np.unravel_index(np.argmax(measured), measured.shape)
    maxima = []
    for rep in range(PLAN["control_replicates"]):
        shuffled = np.zeros_like(pages)
        for page_index, original in enumerate(streams):
            copy = original.copy()
            random.Random(PLAN["control_seed"] + 10000 * rep + page_index).shuffle(copy)
            shuffled[page_index, :len(copy)] = copy
        maxima.append(float(np.max(all_scores(shuffled, lengths, shifts, symbols, sizes, weights))))
    actual = float(measured[winner_index])
    tail = sum(x >= actual for x in maxima)
    return {"schema": "liberpedia-d4v1-positional-totient-results-v1", "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "controls": gate, "settings": len(PLAN["pages"]) * PLAN["operator_count"],
            "source_aligned_pages": len(PLAN["pages"]), "pages": page_rows,
            "score_grid_sha256": hashlib.sha256(measured.astype("<f8", copy=False).tobytes()).hexdigest(),
            "best": {"page": PLAN["pages"][winner_index[0]], "offset": int(winner_index[1]), "score": actual},
            "null_maxima": maxima, "null_at_least_actual": tail,
            "selection_tail_plus_one": (tail + 1) / (len(maxima) + 1)}


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--controls", action="store_true")
    cli.add_argument("--check", action="store_true")
    args = cli.parse_args()
    result = produce(control_only=args.controls)
    if args.controls:
        print(json.dumps(result, indent=2))
        return
    target = HERE / "results.json"
    if args.check:
        if target.read_bytes() != canonical(result):
            raise ValueError("Saved complete-grid result changed")
        print("Complete positional-totient grid, controls and all null maxima match")
    else:
        target.write_bytes(canonical(result))
        print(f"Wrote {target}")


if __name__ == "__main__":
    main()
