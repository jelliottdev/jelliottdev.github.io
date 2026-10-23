"""Bounded whole-page GP-prime plaintext-feedback search.

Numba accelerates the exact finite grid; check.py uses a separate stdlib decoder.
"""
from __future__ import annotations

import argparse
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
BASE = 26 ** 4


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load() -> tuple[dict, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], list[int]]:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for item in plan["inputs"]:
        assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"], item["path"]
    alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    assert len(alphabet) == 29
    lookup = {row["rune"]: i for i, row in enumerate(alphabet)}
    primes = np.array([row["prime"] % 29 for row in alphabet], dtype=np.int64)
    labels = [row["latin"] for row in alphabet]
    symbols = np.zeros((29, 2), dtype=np.int64)
    sizes = np.array([len(label) for label in labels], dtype=np.int64)
    assert all(1 <= n <= 2 for n in sizes)
    for i, label in enumerate(labels):
        for j, letter in enumerate(label):
            symbols[i, j] = ord(letter) - 65
    counts = {}
    for line in (ROOT / plan["score_model"]).read_text(encoding="ascii").splitlines():
        gram, count = line.split()
        counts[gram] = int(count)
    norm = math.log10(sum(counts.values()))
    scores = np.full(BASE, math.log10(.01) - norm, dtype=np.float64)
    for gram, count in counts.items():
        index = 0
        for letter in gram:
            index = index * 26 + ord(letter) - 65
        scores[index] = math.log10(count) - norm
    streams = []
    for page in plan["targets"]:
        text = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        streams.append([lookup[rune] for rune in text if rune in lookup])
    lengths = np.array([len(stream) for stream in streams], dtype=np.int64)
    assert len(streams) == 55 and all(n >= 4 for n in lengths)
    pages = np.zeros((55, int(max(lengths))), dtype=np.int64)
    for i, stream in enumerate(streams):
        pages[i, :len(stream)] = stream
    with (ROOT / "exports/readings/warning.csv").open(encoding="utf-8", newline="") as file:
        warning = [int(row["output_index"]) for row in csv.DictReader(file)]
    assert len(warning) == 184 and all(0 <= value < 29 for value in warning)
    return plan, pages, lengths, primes, symbols, sizes, scores, labels, warning


@njit
def decode_score(cipher, length, arm, seed, sign, primes, symbols, sizes, scores):
    state = seed
    previous = 0
    gram = 0
    letters = 0
    total = 0.0
    for i in range(length):
        if arm == 0:
            key = seed if i == 0 else primes[previous]
        else:
            key = state
        plain = (cipher[i] - sign * key) % 29
        previous = plain
        if arm == 1:
            state = (state + primes[plain]) % 29
        for j in range(sizes[plain]):
            gram = (gram * 26 + symbols[plain, j]) % BASE
            letters += 1
            if letters >= 4:
                total += scores[gram]
    return total / (letters - 3)


@njit
def grid(pages, lengths, primes, symbols, sizes, scores):
    values = np.empty((len(lengths), 2, 29, 2), dtype=np.float64)
    for page in range(len(lengths)):
        for arm in range(2):
            for seed in range(29):
                for sign_index in range(2):
                    sign = -1 if sign_index == 0 else 1
                    values[page, arm, seed, sign_index] = decode_score(
                        pages[page], lengths[page], arm, seed, sign, primes, symbols, sizes, scores)
    return values


def decode(cipher: list[int], arm: int, seed: int, sign: int, primes: list[int]) -> list[int]:
    output = []
    state = seed
    for i, value in enumerate(cipher):
        key = (seed if i == 0 else primes[output[-1]]) if arm == 0 else state
        plain = (value - sign * key) % 29
        output.append(plain)
        if arm == 1:
            state = (state + primes[plain]) % 29
    return output


def encrypt(plain: list[int], arm: int, seed: int, sign: int, primes: list[int]) -> list[int]:
    cipher = []
    state = seed
    for i, value in enumerate(plain):
        key = (seed if i == 0 else primes[plain[i - 1]]) if arm == 0 else state
        cipher.append((value + sign * key) % 29)
        if arm == 1:
            state = (state + primes[value]) % 29
    return cipher


def best_case(values: np.ndarray, targets: list[str]) -> dict:
    index = np.unravel_index(int(np.argmax(values)), values.shape)
    page, arm, seed, sign_index = map(int, index)
    return {"page": targets[page], "arm": ["previous_plaintext_prime", "cumulative_plaintext_prime"][arm],
            "seed": seed, "sign": [-1, 1][sign_index], "score": float(values[index])}


def report() -> tuple[dict, list[dict]]:
    plan, pages, lengths, primes, symbols, sizes, scores, labels, warning = load()
    target = plan["targets"]
    raw_plan = (HERE / "plan.json").read_bytes()
    prime_list = primes.tolist()
    # This verifies the full inversion domain before any LP2 score is inspected.
    controls = []
    for arm in range(2):
        for seed in range(29):
            for sign in (-1, 1):
                cipher = encrypt(warning, arm, seed, sign, prime_list)
                assert decode(cipher, arm, seed, sign, prime_list) == warning
                if seed in (0, 7, 28):
                    planted = np.zeros((1, len(cipher)), dtype=np.int64)
                    planted[0, :] = cipher
                    values = grid(planted, np.array([len(cipher)], dtype=np.int64), primes, symbols, sizes, scores)
                    top = best_case(values, ["plant"])
                    top_arm = plan["arms"].index(top["arm"])
                    top_plain = decode(cipher, top_arm, top["seed"], top["sign"], prime_list)
                    passed = top_plain == warning
                    controls.append({"arm": plan["arms"][arm], "seed": seed, "sign": sign,
                                     "top": top, "top_exact_plaintext": passed})
                    if not passed:
                        raise AssertionError(f"Model selection control failed: {arm=} {seed=} {sign=}")
    observed = grid(pages, lengths, primes, symbols, sizes, scores)
    cases = []
    for p, page in enumerate(target):
        cipher = pages[p, :lengths[p]].tolist()
        for arm in range(2):
            for seed in range(29):
                for sign_index, sign in enumerate((-1, 1)):
                    plain = decode(cipher, arm, seed, sign, prime_list)
                    latin = "".join(labels[value] for value in plain)
                    cases.append({"page": page, "arm": plan["arms"][arm], "seed": seed, "sign": sign,
                                  "score": float(observed[p, arm, seed, sign_index]),
                                  "plaintext_sha256": sha(bytes(plain)), "latin_preview": latin[:80]})
    observed_best = best_case(observed, target)
    per_page = [best_case(observed[i:i + 1], [page]) for i, page in enumerate(target)]
    nulls = []
    for trial_seed in range(33017200, 33017399):
        shuffled = pages.copy()
        rng = random.Random(trial_seed)
        for p in range(len(target)):
            values = shuffled[p, :lengths[p]].tolist()
            rng.shuffle(values)
            shuffled[p, :lengths[p]] = values
        distribution = grid(shuffled, lengths, primes, symbols, sizes, scores)
        nulls.append({"shuffle_seed": trial_seed,
                      "shuffled_streams_sha256": sha(b"".join(bytes(shuffled[p, :lengths[p]].tolist()) + b"\n" for p in range(len(target)))),
                      **best_case(distribution, target)})
    result = {
        "schema": "liberpedia-gp-prime-plaintext-feedback-results-v1",
        "plan_sha256": sha(raw_plan), "candidate_count": len(cases),
        "model_control": {"roundtrips": 2 * 29 * 2, "selected_plants": controls,
                          "all_selected_plants_exact": all(row["top_exact_plaintext"] for row in controls)},
        "observed_global_best": observed_best, "observed_page_best": per_page,
        "null_global_maxima": nulls,
        "null_exceedances": sum(row["score"] >= observed_best["score"] for row in nulls),
        "null_trials": len(nulls),
        "cases_sha256": ""
    }
    return result, cases


def case_bytes(cases: list[dict]) -> bytes:
    fields = ["page", "arm", "seed", "sign", "score", "plaintext_sha256", "latin_preview"]
    import io
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(cases)
    return stream.getvalue().encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result, cases = report()
    data = case_bytes(cases)
    result["cases_sha256"] = sha(data)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert (HERE / "cases.csv").read_bytes() == data
        assert (HERE / "results.json").read_text(encoding="utf-8") == output
        print("PASS: all 6,380 cases, 116 inversions, 12 selected plants and 199 global null grids")
    else:
        (HERE / "cases.csv").write_bytes(data)
        (HERE / "results.json").write_text(output, encoding="utf-8", newline="\n")
        print(json.dumps({"winner": result["observed_global_best"], "null_exceedances": result["null_exceedances"]}))


if __name__ == "__main__":
    main()
