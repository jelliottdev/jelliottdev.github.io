"""Bounded full-page GP29 search using Cicada public-key packet material."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np

from engine import search, score_one, BASE
from material import materials

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
PINS = {row["path"]: row["sha256"] for row in PLAN["inputs"]}
ARMOR = "experiments/records/public-rsa-payload-e01/source/corpus/A-primary-artifacts/pgp/keys/cicada-3301-pubkey.keys.openpgp.org.asc"


def source(relative):
    raw = (ROOT / relative).read_bytes()
    if hashlib.sha256(raw).hexdigest() != PINS[relative]:
        raise ValueError(f"Changed source: {relative}")
    return raw


def setup():
    extracted = materials(source(ARMOR))
    assert [name for name, _, _ in extracted] == ["primary", "subkey"]
    for name, body, fingerprint in extracted:
        assert fingerprint.hex() == PLAN["expected_fingerprints"][name]
        assert len(body) == 525 and len(fingerprint) == 20
    material_rows = [("primary-packet", extracted[0][1]),
                     ("primary-fingerprint", extracted[0][2]),
                     ("subkey-packet", extracted[1][1]),
                     ("subkey-fingerprint", extracted[1][2])]
    assert [name for name, _ in material_rows] == PLAN["key_order"]
    periods = np.array([len(raw) for _, raw in material_rows], dtype=np.int64)
    starts = np.array([sum(periods[:i]) for i in range(4)], dtype=np.int64)
    keyflat = np.array([byte % 29 for _, raw in material_rows for byte in raw], dtype=np.int64)
    alphabet = json.loads(source("data/index.json"))["alphabet"]
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, row in enumerate(alphabet):
        label = row["latin"]
        sizes[i] = len(label)
        for j, letter in enumerate(label):
            symbols[i, j] = ord(letter) - 65
    counts = {}
    for line in source(PLAN["score_model"]).decode("ascii").splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    normalizer = math.log10(sum(counts.values()))
    weights = np.full(BASE, math.log10(0.01) - normalizer, dtype=np.float64)
    for gram, amount in counts.items():
        state = 0
        for letter in gram:
            state = state * 26 + ord(letter) - 65
        weights[state] = math.log10(amount) - normalizer
    return material_rows, periods, starts, keyflat, lookup, alphabet, symbols, sizes, weights


def setting_at(column, periods):
    column = int(column)
    for group, n in enumerate(periods):
        span = 2 * int(n)
        if column < span:
            return group, column // 2, -1 if column % 2 == 0 else 1
        column -= span
    raise IndexError(column)


def control_gate(settings):
    material_rows, periods, starts, keyflat, lookup, alphabet, symbols, sizes, weights = settings
    zero = np.zeros(1, dtype=np.int64)
    rows = []
    for number, name in enumerate(PLAN["controls"]["readings"]):
        trace = source(f"exports/readings/{name}.csv").decode("utf-8-sig")
        plain = np.array([int(row["output_index"]) for row in csv.DictReader(trace.splitlines())][:66], dtype=np.int64)
        assert len(plain) == 66
        original_score = score_one(plain, zero, 0, 1, symbols, sizes, weights)
        group = number % 4
        key = keyflat[starts[group]:starts[group] + periods[group]]
        phase = (31 * number + 7) % len(key)
        sign = -1 if number % 2 == 0 else 1
        coded = np.array([(int(p) - sign * int(key[(i + phase) % len(key)])) % 29
                          for i, p in enumerate(plain)], dtype=np.int64)
        decoded = np.array([(int(c) + sign * int(key[(i + phase) % len(key)])) % 29
                            for i, c in enumerate(coded)], dtype=np.int64)
        recovered = np.array_equal(decoded, plain)
        recovered_score = score_one(coded, key, phase, sign, symbols, sizes, weights)
        assert recovered and abs(recovered_score - original_score) < 1e-11
        rows.append({"reading": name, "score": original_score, "material": material_rows[group][0],
                     "phase": int(phase), "sign": sign, "exact_recovery": recovered})
    passed = sum(row["score"] >= PLAN["score_threshold"] for row in rows) >= 8 and all(row["exact_recovery"] for row in rows)
    return {"rows": rows, "passed": passed, "readings_above_threshold": sum(row["score"] >= PLAN["score_threshold"] for row in rows)}


def score_crosschecks(pages, lengths, settings):
    material_rows, periods, starts, keyflat, lookup, alphabet, symbols, sizes, weights = settings
    labels = [row["latin"] for row in alphabet]
    table = {}
    for line in source(PLAN["score_model"]).decode("ascii").splitlines():
        gram, count = line.split()
        table[gram] = int(count)
    norm = math.log10(sum(table.values()))
    floor = math.log10(0.01) - norm
    rows = []
    for number in range(9):
        page = (number * 7 + 2) % len(lengths)
        group = number % 4
        key = keyflat[starts[group]:starts[group] + periods[group]]
        phase = (number * 43 + 3) % len(key)
        sign = -1 if number % 2 else 1
        cipher = pages[page, :lengths[page]]
        plain = [(int(c) + sign * int(key[(i + phase) % len(key)])) % 29 for i, c in enumerate(cipher)]
        text = "".join(labels[index] for index in plain)
        expected = sum(math.log10(table[gram]) - norm if gram in table else floor
                       for gram in (text[i:i + 4] for i in range(len(text) - 3))) / (len(text) - 3)
        actual = score_one(cipher, key, phase, sign, symbols, sizes, weights)
        assert abs(expected - actual) < 1e-11
        rows.append({"page": PLAN["pages"][page], "material": material_rows[group][0],
                     "phase": int(phase), "sign": sign, "score": actual})
    return rows


def produce(controls_only=False):
    settings = setup()
    gate = control_gate(settings)
    if controls_only:
        return gate
    if not gate["passed"]:
        raise ValueError("Known-reading control gate failed; LP2 not scored")
    material_rows, periods, starts, keyflat, lookup, alphabet, symbols, sizes, weights = settings
    page_lists = []
    for name in PLAN["pages"]:
        data = json.loads(source(f"data/pages/{name}.json"))
        cipher = [lookup[r] for line in data["lines"] for r in line["raw"] if r in lookup]
        assert len(cipher) == data["rune_count"] and len(cipher) >= 66
        page_lists.append(cipher)
    assert json.loads(source("data/pages/lp2-50.json"))["rune_count"] == 0
    lengths = np.array([len(row) for row in page_lists], dtype=np.int64)
    pages = np.zeros((len(lengths), max(lengths)), dtype=np.int64)
    for i, row in enumerate(page_lists):
        pages[i, :len(row)] = row
    crosschecks = score_crosschecks(pages, lengths, settings)
    observed = search(pages, lengths, keyflat, starts, periods, symbols, sizes, weights)
    assert observed.shape == (55, 2180)
    best_flat = int(np.argmax(observed))
    best_page, best_column = np.unravel_index(best_flat, observed.shape)
    best_group, best_phase, best_sign = setting_at(best_column, periods)
    winner = {"page": PLAN["pages"][best_page], "material": material_rows[best_group][0],
              "phase": best_phase, "sign": best_sign, "score": float(observed[best_page, best_column])}
    stream_maxima = []
    cursor = 0
    for group, n in enumerate(periods):
        block = observed[:, cursor:cursor + 2 * n]
        flat = int(np.argmax(block))
        p, local = np.unravel_index(flat, block.shape)
        stream_maxima.append({"material": material_rows[group][0], "page": PLAN["pages"][p],
                              "phase": int(local // 2), "sign": -1 if local % 2 == 0 else 1,
                              "score": float(block[p, local])})
        cursor += 2 * n
    page_maxima = [{"page": name, "score": float(observed[i].max())}
                   for i, name in enumerate(PLAN["pages"])]
    null_maxima = []
    for rep in range(PLAN["null"]["replicates"]):
        shuffled = pages.copy()
        for p in range(len(lengths)):
            row = shuffled[p, :lengths[p]].tolist()
            random.Random(PLAN["null"]["seed"] + 1000 * rep + p).shuffle(row)
            shuffled[p, :lengths[p]] = row
        values = search(shuffled, lengths, keyflat, starts, periods, symbols, sizes, weights)
        null_maxima.append(float(values.max()))
    best = winner["score"]
    return {"schema": "liberpedia-pgp-packet-keys-v1",
            "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
            "source": [{"name": name, "length": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                       for name, raw in material_rows],
            "control_gate": gate, "numeric_string_crosschecks": crosschecks,
            "page_count": len(lengths), "case_count": observed.size,
            "score_matrix_sha256": hashlib.sha256(observed.astype("<f8").tobytes()).hexdigest(),
            "threshold_passes": int(np.count_nonzero(observed >= PLAN["score_threshold"])),
            "winner": winner, "stream_maxima": stream_maxima, "page_maxima": page_maxima,
            "null_global_maxima": null_maxima,
            "null_at_least_best": sum(score >= best for score in null_maxima),
            "empirical_global_tail": (1 + sum(score >= best for score in null_maxima)) / (len(null_maxima) + 1)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--controls-only", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = produce(args.controls_only)
    if args.controls_only:
        print({"passed": result["passed"], "readings_above_threshold": result["readings_above_threshold"]})
    elif args.check:
        assert result == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: complete four-material full-page search and 199 null maxima")
    else:
        (HERE / "results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print({key: result[key] for key in ("case_count", "threshold_passes", "winner", "null_at_least_best")})
