"""Complete page-local linear-clock Caesar search with a global selection control."""
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
QUADS = 26 ** 4


def source(path):
    name = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUTS[name]:
        raise ValueError(f"Input changed: {name}")
    return raw


@njit
def numeric_score(cipher, k, b, symbols, sizes, weights):
    state = 0
    chars = 0
    amount = 0.0
    for position in range(len(cipher)):
        value = (cipher[position] + k * position + b) % 29
        for j in range(sizes[value]):
            state = (state * 26 + symbols[value, j]) % QUADS
            chars += 1
            if chars >= 4:
                amount += weights[state]
    return amount / (chars - 3)


@njit
def score_grid(pages, lengths, symbols, sizes, weights):
    scores = np.empty((len(lengths), 812), dtype=np.float64)
    for page in range(len(lengths)):
        cipher = pages[page, :lengths[page]]
        for k in range(1, 29):
            for b in range(29):
                scores[page, (k - 1) * 29 + b] = numeric_score(cipher, k, b, symbols, sizes, weights)
    return scores


@njit
def grid_max(pages, lengths, symbols, sizes, weights):
    best = -1e300
    for page in range(len(lengths)):
        cipher = pages[page, :lengths[page]]
        for k in range(1, 29):
            for b in range(29):
                value = numeric_score(cipher, k, b, symbols, sizes, weights)
                if value > best:
                    best = value
    return best


def setup():
    alphabet = json.loads(source(ROOT / "data/index.json"))["alphabet"]
    lookup = {row["rune"]: index for index, row in enumerate(alphabet)}
    labels = [row["latin"] for row in alphabet]
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, letters in enumerate(labels):
        sizes[i] = len(letters)
        for j, letter in enumerate(letters):
            symbols[i, j] = ord(letter) - 65
    model = [line.split() for line in source(ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
    total = sum(int(n) for _, n in model)
    floor = math.log10(0.01 / total)
    weights = np.full(QUADS, floor, dtype=np.float64)
    table = {}
    for gram, n in model:
        value = math.log10(int(n) / total)
        table[gram] = value
        state = 0
        for letter in gram:
            state = state * 26 + ord(letter) - 65
        weights[state] = value

    def portable_score(indices):
        text = "".join(labels[x] for x in indices)
        return sum(table.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)

    return lookup, labels, symbols, sizes, weights, portable_score


def controls(portable_score):
    rows = []
    k = PLAN["positive_control_schedule"]["k"]
    b = PLAN["positive_control_schedule"]["b"]
    for number, name in enumerate(PLAN["readings"]):
        data = source(ROOT / f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = [int(row["output_index"]) for row in csv.DictReader(data.splitlines())]
        if len(plain) < 66:
            raise ValueError(f"Short solved reading: {name}")
        direct = portable_score(plain)
        shuffles_below = 0
        for rep in range(PLAN["control_replicates"]):
            values = plain.copy()
            random.Random(PLAN["control_seed"] + 1000 * number + rep).shuffle(values)
            shuffles_below += portable_score(values) < direct
        cipher = [(value - k * pos - b) % 29 for pos, value in enumerate(plain)]
        ranked = sorted(((portable_score([(c + candidate_k * pos + candidate_b) % 29
                                          for pos, c in enumerate(cipher)]), candidate_k, candidate_b)
                         for candidate_k in range(1, 29) for candidate_b in range(29)),
                        key=lambda row: (-row[0], row[1], row[2]))
        true_rank = next(position + 1 for position, row in enumerate(ranked) if row[1:] == (k, b))
        assert [(c + k * pos + b) % 29 for pos, c in enumerate(cipher)] == plain
        rows.append({"reading": name, "runes": len(plain), "source_score": direct,
                     "shuffles_below": shuffles_below, "planted_true_rank": true_rank})
    originals = sum(row["source_score"] >= PLAN["score_threshold"] and row["shuffles_below"] >= 198 for row in rows)
    plants = sum(row["planted_true_rank"] == 1 for row in rows)
    return {"rows": rows, "good_originals": originals, "top_rank_plants": plants,
            "passed": originals >= 8 and plants >= 8}


def page_arrays(lookup):
    streams = []
    for name in PLAN["pages"]:
        doc = json.loads(source(ROOT / f"data/pages/{name}.json"))
        values = [lookup[rune] for line in doc["lines"] for rune in line["raw"] if rune in lookup]
        assert len(values) == doc["rune_count"] and len(values) >= 66
        streams.append(values)
    assert json.loads(source(ROOT / "data/pages/lp2-50.json"))["rune_count"] == 0
    lengths = np.array([len(x) for x in streams], dtype=np.int64)
    pages = np.zeros((len(streams), int(max(lengths))), dtype=np.int64)
    for index, values in enumerate(streams):
        pages[index, :len(values)] = values
    return streams, pages, lengths


def produce(control_only=False):
    lookup, labels, symbols, sizes, weights, portable_score = setup()
    gate = controls(portable_score)
    if control_only:
        return gate, None
    if not gate["passed"]:
        raise ValueError("Predeclared control gate failed; manuscript not scored")
    streams, pages, lengths = page_arrays(lookup)
    grid = score_grid(pages, lengths, symbols, sizes, weights)
    # The compiled numeric scorer must reproduce the portable Latin-string rule.
    for page_index, k, b in ((0, 1, 0), (0, 28, 28), (14, 7, 13),
                             (31, 12, 3), (48, 28, 0), (54, 5, 21)):
        plain = [(c + k * pos + b) % 29 for pos, c in enumerate(streams[page_index])]
        assert math.isclose(grid[page_index, (k - 1) * 29 + b], portable_score(plain), abs_tol=1e-11)
    cases = []
    for page_index, (name, cipher) in enumerate(zip(PLAN["pages"], streams)):
        for k in range(1, 29):
            for b in range(29):
                clear = bytes((c + k * pos + b) % 29 for pos, c in enumerate(cipher))
                cases.append({"page": name, "k": k, "b": b,
                              "score": float(grid[page_index, (k - 1) * 29 + b]),
                              "output_sha256": hashlib.sha256(clear).hexdigest()})
    maxima = []
    for rep in range(PLAN["null_replicates"]):
        randomized = np.zeros_like(pages)
        for page_index, values in enumerate(streams):
            rearranged = values.copy()
            random.Random(PLAN["null_seed"] + 1000 * rep + page_index).shuffle(rearranged)
            randomized[page_index, :len(rearranged)] = rearranged
        maxima.append(float(grid_max(randomized, lengths, symbols, sizes, weights)))
    case_lines = "".join(json.dumps(case, separators=(",", ":")) + "\n" for case in cases)
    winner = max(cases, key=lambda x: (x["score"], -int(x["page"][4:]), -x["k"], -x["b"]))
    at_least = sum(score >= winner["score"] for score in maxima)
    result = {"schema": "liberpedia-wholepage-progressive-caesar-v1",
              "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
              "control_gate": gate, "page_count": len(streams), "case_count": len(cases),
              "cases_sha256": hashlib.sha256(case_lines.encode("utf-8")).hexdigest(),
              "best_case": winner,
              "threshold_passes": int(np.count_nonzero(grid >= PLAN["score_threshold"])),
              "null_maxima": maxima, "null_at_least_best": at_least,
              "empirical_global_tail": (1 + at_least) / (len(maxima) + 1)}
    return result, case_lines


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--controls-only", action="store_true")
    args = parser.parse_args()
    result, case_lines = produce(args.controls_only)
    if args.controls_only:
        print(json.dumps({k: result[k] for k in ("good_originals", "top_rank_plants", "passed")}))
    elif args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        assert case_lines == (HERE / "cases.jsonl").read_text(encoding="utf-8")
        print("PASS: full progressive-shift grid and global null match saved files")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        (HERE / "cases.jsonl").write_text(case_lines, encoding="utf-8", newline="\n")
        print(json.dumps({k: result[k] for k in ("case_count", "best_case", "threshold_passes", "null_at_least_best", "empirical_global_tail")}))
