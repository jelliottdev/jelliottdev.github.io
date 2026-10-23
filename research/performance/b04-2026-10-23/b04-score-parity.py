"""Check reusable numeric scorer against B04 source score, no beam replacement."""
import hashlib
import json
import math
import pathlib
import random
import sys
import time

import numpy as np
from numba import njit

import argparse

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--source-root", type=pathlib.Path, required=True)
_parser.add_argument("--output", type=pathlib.Path)
_args = _parser.parse_args()
SOURCE = _args.source_root.resolve()
sys.path.insert(0, str(SOURCE / "liber-primus/analysis/round13/B04"))
sys.path.insert(0, str(SOURCE / "liber-primus/analysis/campaign18_skip"))
sys.path.insert(0, str(SOURCE / "liber-primus/src"))
import skipdecode as sk  # noqa: E402
from lp import gematria as gp  # noqa: E402

OUT = _args.output or pathlib.Path(__file__).with_name("b04-score-parity-20261023.json")
BASE = 26 ** 4


@njit
def score_indices(indices, symbols, sizes, probabilities):
    state = 0
    chars = 0
    score = 0.0
    for idx in indices:
        for j in range(sizes[idx]):
            state = (state * 26 + symbols[idx, j]) % BASE
            chars += 1
            if chars >= 4:
                score += probabilities[state]
    if chars < 4:
        return -999.0
    return score / (chars - 3)


def model_arrays():
    symbols = np.zeros((29, 3), dtype=np.int64)
    sizes = np.zeros(29, dtype=np.int64)
    for i, label in gp.IDX_TO_TRANS.items():
        sizes[i] = len(label)
        for j, letter in enumerate(label):
            symbols[i, j] = ord(letter) - ord("A")
    probabilities = np.full(BASE, sk.Q.floor, dtype=np.float64)
    for gram, score in sk.Q.d.items():
        state = 0
        for letter in gram:
            state = state * 26 + ord(letter) - ord("A")
        probabilities[state] = score
    return symbols, sizes, probabilities


def main():
    symbols, sizes, probabilities = model_arrays()
    phrase = sk.eng_to_idx("THE PRIMES ARE SACRED AND THE PILGRIM SEEKS THE TRUTH")
    rows = []
    for length in (100, 120, 262, 1024, 12956):
        for kind in ("plain", "random"):
            rng = random.Random(3301 + length)
            idx = np.array((phrase * math.ceil(length / len(phrase)))[:length] if kind == "plain"
                           else [rng.randrange(29) for _ in range(length)], dtype=np.int64)
            t0 = time.perf_counter()
            observed = float(score_indices(idx, symbols, sizes, probabilities))
            compiled_time = time.perf_counter() - t0
            t1 = time.perf_counter()
            expected = sk.Q.score_norm(sk.idx_to_trans(idx.tolist()))
            source_time = time.perf_counter() - t1
            assert math.isclose(observed, expected, rel_tol=0, abs_tol=1e-11)
            rows.append({"runes": length, "kind": kind, "source_score": expected,
                         "numeric_score": observed, "abs_difference": abs(observed - expected),
                         "source_score_s": source_time, "compiled_score_s": compiled_time})
            print(length, kind, expected, observed, source_time, compiled_time, flush=True)
    model_file = SOURCE / "liber-primus/data/english_quadgrams.txt"
    OUT.write_text(json.dumps({"source_commit": "f08b20b", "mode": "final_scores_only_no_beam",
                               "model_sha256": hashlib.sha256(model_file.read_bytes()).hexdigest(),
                               "rows": rows}, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(OUT)


if __name__ == "__main__":
    main()
