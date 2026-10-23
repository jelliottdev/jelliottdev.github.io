"""Complete zero-offset page-pair arithmetic English-score grid."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SPACE = 26 ** 4


@njit
def score_pair(a, b, symbols, sizes, frequencies):
    """Score all three arithmetic streams in one pass through an aligned pair."""
    states = np.zeros(3, dtype=np.int64)
    lengths = np.zeros(3, dtype=np.int64)
    totals = np.zeros(3, dtype=np.float64)
    count = min(len(a), len(b))
    for pos in range(count):
        x, y = a[pos], b[pos]
        for arm in range(3):
            symbol = (x + y) % 29 if arm == 0 else ((x - y) % 29 if arm == 1 else (y - x) % 29)
            for col in range(sizes[symbol]):
                states[arm] = (states[arm] * 26 + symbols[symbol, col]) % SPACE
                lengths[arm] += 1
                if lengths[arm] >= 4:
                    totals[arm] += frequencies[states[arm]]
    scores = np.empty(3, dtype=np.float64)
    quads = np.empty(3, dtype=np.int64)
    for arm in range(3):
        quads[arm] = max(0, lengths[arm] - 3)
        scores[arm] = totals[arm] / quads[arm] if quads[arm] >= 100 else -1e300
    return scores, quads


@njit
def grid(pages, lengths, symbols, sizes, frequencies):
    output = np.empty((len(lengths) * (len(lengths) - 1) // 2, 3), dtype=np.float64)
    groups = np.empty_like(output, dtype=np.int64)
    row = 0
    for left in range(len(lengths)):
        for right in range(left + 1, len(lengths)):
            scores, quads = score_pair(pages[left, :lengths[left]], pages[right, :lengths[right]],
                                       symbols, sizes, frequencies)
            output[row] = scores
            groups[row] = quads
            row += 1
    return output, groups


def load():
    plan_raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"], item["path"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    index = {entry["rune"]: n for n, entry in enumerate(alphabet)}
    labels = [entry["latin"] for entry in alphabet]
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for n, label in enumerate(labels):
        sizes[n] = len(label)
        for col, ch in enumerate(label):
            symbols[n, col] = ord(ch) - 65
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    normalizer = math.log10(sum(counts.values()))
    frequencies = np.full(SPACE, math.log10(0.01) - normalizer, dtype=np.float64)
    for gram, amount in counts.items():
        slot = 0
        for ch in gram:
            slot = slot * 26 + ord(ch) - 65
        frequencies[slot] = math.log10(amount) - normalizer
    page_lists = []
    for page in plan["targets"]:
        raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        page_lists.append([index[ch] for ch in raw if ch in index])
    lengths = np.array([len(page) for page in page_lists], dtype=np.int64)
    assert len(page_lists) == 55 and all(lengths)
    pages = np.zeros((55, max(lengths)), dtype=np.int64)
    for row, values in enumerate(page_lists):
        pages[row, :len(values)] = values
    return plan, plan_raw, pages, lengths, symbols, sizes, frequencies, labels


def shuffled_pages(pages, lengths, seed):
    rng = random.Random(seed)
    edges = [[0] + sorted({int(other) for other in lengths if other <= own}) for own in lengths]
    copy = pages.copy()
    for row, limits in enumerate(edges):
        for start, end in zip(limits, limits[1:]):
            band = copy[row, start:end].tolist()
            rng.shuffle(band)
            copy[row, start:end] = band
    return copy


def controls(plan, symbols, sizes, frequencies, labels):
    readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    warning = next(item for item in readings["controls"] if item["id"] == "warning")
    desired = [index for page in warning["decoded_pages"] for index in page["rune_indices"]]
    assert len(desired) == 184
    rng = random.Random(33017126)
    first = [rng.randrange(29) for _ in desired]
    outcomes = {}
    for arm in range(3):
        if arm == 0:
            second = [(p - a) % 29 for a, p in zip(first, desired)]
            recovered = [(a + b) % 29 for a, b in zip(first, second)]
        elif arm == 1:
            second = [(a - p) % 29 for a, p in zip(first, desired)]
            recovered = [(a - b) % 29 for a, b in zip(first, second)]
        else:
            second = [(p + a) % 29 for a, p in zip(first, desired)]
            recovered = [(b - a) % 29 for a, b in zip(first, second)]
        assert recovered == desired
        scores, quads = score_pair(np.array(first, dtype=np.int64), np.array(second, dtype=np.int64),
                                   symbols, sizes, frequencies)
        assert quads[arm] >= 100 and scores[arm] > -5.5, (arm, scores[arm])
        outcomes[plan["operations"][arm]] = {"score": float(scores[arm]), "quadgrams": int(quads[arm]),
                                             "exact_indices": True}
    for a in range(29):
        for b in range(29):
            assert (a + b) % 29 == (b + a) % 29
            assert ((a - b) + (b - a)) % 29 == 0
    return outcomes


def report():
    plan, raw, pages, lengths, symbols, sizes, frequencies, labels = load()
    planted = controls(plan, symbols, sizes, frequencies, labels)
    observed, quads = grid(pages, lengths, symbols, sizes, frequencies)
    pairs = [(i, j) for i in range(55) for j in range(i + 1, 55)]
    eligible = int(np.count_nonzero(quads >= 100))
    assert len(pairs) == 1485 and eligible > 0
    at = int(np.argmax(observed))
    best_pair, best_arm = divmod(at, 3)
    left, right = pairs[best_pair]
    n = min(lengths[left], lengths[right])
    if best_arm == 0:
        values = (pages[left, :n] + pages[right, :n]) % 29
    elif best_arm == 1:
        values = (pages[left, :n] - pages[right, :n]) % 29
    else:
        values = (pages[right, :n] - pages[left, :n]) % 29
    output = "".join(labels[int(index)] for index in values)
    cases = []
    for row, (i, j) in enumerate(pairs):
        for arm, operation in enumerate(plan["operations"]):
            cases.append({"page_a": plan["targets"][i], "page_b": plan["targets"][j],
                          "operation": operation, "compared_runes": int(min(lengths[i], lengths[j])),
                          "quadgrams": int(quads[row, arm]),
                          "score": float(observed[row, arm]) if quads[row, arm] >= 100 else None})
    nulls = []
    for trial in range(256):
        seed = 33017127 + trial
        shuffled = shuffled_pages(pages, lengths, seed)
        scores, groups = grid(shuffled, lengths, symbols, sizes, frequencies)
        where = int(np.argmax(scores))
        pair_index, arm = divmod(where, 3)
        i, j = pairs[pair_index]
        nulls.append({"seed": seed, "score": float(scores[pair_index, arm]),
                      "page_a": plan["targets"][i], "page_b": plan["targets"][j],
                      "operation": plan["operations"][arm],
                      "eligible": int(np.count_nonzero(groups >= 100))})
    best_score = float(observed[best_pair, best_arm])
    exceed = sum(case["score"] >= best_score for case in nulls)
    return {
        "schema": "liberpedia-page-pair-english-v1",
        "plan_sha256": hashlib.sha256(raw).hexdigest(),
        "page_count": 55, "pair_count": 1485, "case_count": len(cases), "eligible_cases": eligible,
        "page_lengths": {name: int(length) for name, length in zip(plan["targets"], lengths)},
        "planted_controls": planted,
        "observed_best": {"page_a": plan["targets"][left], "page_b": plan["targets"][right],
                          "operation": plan["operations"][best_arm], "score": best_score,
                          "compared_runes": int(n), "quadgrams": int(quads[best_pair, best_arm]),
                          "latin": output},
        "observed_cases": cases,
        "null_global_maxima": nulls,
        "null_at_or_above_observed": exceed,
        "empirical_global_p": (1 + exceed) / 257,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    actual = report()
    destination = HERE / "results.json"
    if args.check:
        assert actual == json.loads(destination.read_text(encoding="utf-8"))
        print("PASS: 4,455 page-pair arithmetic candidates and 256 full-grid conditional shuffles")
    else:
        destination.write_text(json.dumps(actual, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(actual["observed_best"])
        print("null exceedances:", actual["null_at_or_above_observed"])
