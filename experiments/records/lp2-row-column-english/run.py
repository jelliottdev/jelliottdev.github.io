"""Full-stream English score of all 16 published ragged row/column routes."""
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
def score_routes(pages, owners, route_orders, route_lengths, labels, sizes, table):
    values = np.empty(len(owners), np.float64)
    quadgrams = np.empty(len(owners), np.int64)
    for case in range(len(owners)):
        state = 0
        characters = 0
        total = 0.0
        for position in range(route_lengths[case]):
            symbol = pages[owners[case], route_orders[case, position]]
            for col in range(sizes[symbol]):
                state = (state * 26 + labels[symbol, col]) % SPACE
                characters += 1
                if characters >= 4:
                    total += table[state]
        groups = max(0, characters - 3)
        quadgrams[case] = groups
        values[case] = total / groups if groups >= 100 else -1e300
    return values, quadgrams


def load():
    raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(raw)
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"], item["path"]
    alpha = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    labels = np.zeros((29, 2), np.int64)
    sizes = np.zeros(29, np.int64)
    for n, item in enumerate(alpha):
        sizes[n] = len(item["latin"])
        for col, ch in enumerate(item["latin"]):
            labels[n, col] = ord(ch) - 65
    counts = {}
    for line in (ROOT / plan["model"]).read_text(encoding="ascii").splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    divisor = math.log10(sum(counts.values()))
    table = np.full(SPACE, math.log10(0.01) - divisor, np.float64)
    for gram, amount in counts.items():
        idx = 0
        for letter in gram:
            idx = idx * 26 + ord(letter) - 65
        table[idx] = math.log10(amount) - divisor
    route_data = json.loads((ROOT / "experiments/records/lp2-row-column-routes/results.json").read_text(encoding="utf-8"))
    source_pages = []
    metadata = []
    route_arrays = []
    owners = []
    for page in route_data["pages"]:
        if page["page"] not in plan["targets"]:
            continue
        owner = len(source_pages)
        source = [item["index"] for item in page["source_positions"]]
        source_pages.append(source)
        assert len(page["cases"]) == 16
        for case in page["cases"]:
            order = case["source_ordinals"]
            assert sorted(order) == list(range(len(source)))
            assert [source[index] for index in order] == case["output_indices"]
            route_arrays.append(order)
            owners.append(owner)
            metadata.append({"page": page["page"], "axis": case["axis"],
                             "outer_reverse": case["outer_reverse"],
                             "inner_reverse": case["inner_reverse"], "alternating": case["alternating"]})
    assert len(source_pages) == 55 and len(route_arrays) == 880
    page_values = np.zeros((55, max(map(len, source_pages))), np.int64)
    page_lengths = []
    for n, values in enumerate(source_pages):
        page_values[n, :len(values)] = values
        page_lengths.append(len(values))
    route_values = np.zeros((880, page_values.shape[1]), np.int64)
    route_lengths = np.asarray([len(route) for route in route_arrays], np.int64)
    for n, route in enumerate(route_arrays):
        route_values[n, :len(route)] = route
    return (plan, raw, page_values, page_lengths, np.asarray(owners, np.int64),
            route_values, route_lengths, metadata, labels, sizes, table, alpha)


def shuffled(pages, page_lengths, seed):
    rng = random.Random(seed)
    output = pages.copy()
    for row, length in enumerate(page_lengths):
        permutation = output[row, :length].tolist()
        rng.shuffle(permutation)
        output[row, :length] = permutation
    return output


def controls(plan, page_values, page_lengths, owners, orders, route_lengths, labels, sizes, table):
    readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
    welcome = next(item for item in readings["controls"] if item["id"] == "welcome")
    known = [symbol for page in welcome["decoded_pages"] for symbol in page["rune_indices"]]
    page_no = plan["targets"].index("lp2-31")
    length = page_lengths[page_no]
    assert length == 269 and len(known) >= length
    known = known[:length]
    planted_scores = []
    for route in range(page_no * 16, (page_no + 1) * 16):
        order = orders[route, :length]
        placed = np.zeros(length, np.int64)
        for output_pos, original_pos in enumerate(order):
            placed[original_pos] = known[output_pos]
        assert [int(placed[original_pos]) for original_pos in order] == known
        carrier = np.zeros_like(page_values)
        carrier[page_no, :length] = placed
        values, groups = score_routes(carrier, owners[route:route+1], orders[route:route+1],
                                       route_lengths[route:route+1], labels, sizes, table)
        assert int(groups[0]) >= 100 and float(values[0]) > -5.5
        planted_scores.append(float(values[0]))
    # Uneven-row hand checks, separately from the archived routes.
    ragged = [["A", "B", "C"], ["D", "E"], ["F"]]
    assert "".join(row[col] for col in range(3) for row in ragged if col < len(row)) == "ADFBEC"
    assert "".join("".join(row if i % 2 == 0 else row[::-1]) for i, row in enumerate(ragged)) == "ABCEDF"
    return {"route_count": 16, "min_score": min(planted_scores), "max_score": max(planted_scores),
            "exact_inverse_recovery": True, "source": "welcome", "runes": length}


def report():
    (plan, raw, pages, page_lengths, owners, orders, route_lengths, metadata,
     labels, sizes, table, alphabet) = load()
    planted = controls(plan, pages, page_lengths, owners, orders, route_lengths, labels, sizes, table)
    observed, groups = score_routes(pages, owners, orders, route_lengths, labels, sizes, table)
    best = int(np.argmax(observed))
    owner = owners[best]
    stream = [int(pages[owner, index]) for index in orders[best, :route_lengths[best]]]
    text = "".join(alphabet[index]["latin"] for index in stream)
    observed_cases = [dict(metadata[n], runes=int(route_lengths[n]), quadgrams=int(groups[n]),
                           score=float(observed[n]) if groups[n] >= 100 else None)
                      for n in range(len(owners))]
    nulls = []
    for trial in range(256):
        seed = 33017128 + trial
        random_pages = shuffled(pages, page_lengths, seed)
        values, counts = score_routes(random_pages, owners, orders, route_lengths, labels, sizes, table)
        winner = int(np.argmax(values))
        nulls.append(dict(metadata[winner], seed=seed, score=float(values[winner]),
                          eligible_cases=int(np.count_nonzero(counts >= 100))))
    count = sum(item["score"] >= float(observed[best]) for item in nulls)
    return {"schema": "liberpedia-row-column-english-v1",
            "plan_sha256": hashlib.sha256(raw).hexdigest(),
            "page_count": 55, "parameter_routes": len(owners),
            "eligible_routes": int(np.count_nonzero(groups >= 100)),
            "page_lengths": dict(zip(plan["targets"], page_lengths)),
            "planted_controls": planted,
            "observed_best": dict(metadata[best], runes=len(stream), quadgrams=int(groups[best]),
                                  score=float(observed[best]), latin=text),
            "observed_cases": observed_cases,
            "null_global_maxima": nulls,
            "null_at_or_above_observed": count,
            "empirical_global_p": (1+count)/257}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    current = report()
    path = HERE / "results.json"
    if args.check:
        assert current == json.loads(path.read_text(encoding="utf-8"))
        print("PASS: 880 routes, 16 planted controls, 256 matched full-route searches")
    else:
        path.write_text(json.dumps(current, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(current["observed_best"])
        print("null at/above:", current["null_at_or_above_observed"])
