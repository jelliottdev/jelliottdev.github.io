"""Independent complete-grid check using coprime totients and assembled text."""
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
SAVED = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
INPUTS = {row["path"]: row["sha256"] for row in PLAN["inputs"]}


def pinned(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == INPUTS[path], path
    return data


def phi_coprime(n):
    return sum(math.gcd(n, candidate) == 1 for candidate in range(1, n + 1)) if n else 0


@njit
def alternate_score(cipher, shifts, token_lengths, token_letters, model):
    # Build the whole candidate text first, then inspect separate four-letter windows.
    letters = np.empty(len(cipher) * 2, dtype=np.int64)
    used = 0
    for i in range(len(cipher)):
        decoded = (cipher[i] - shifts[i] + 29) % 29
        for j in range(token_lengths[decoded]):
            letters[used] = token_letters[decoded, j]
            used += 1
    total = 0.0
    for i in range(used - 3):
        key = ((letters[i] * 26 + letters[i + 1]) * 26 + letters[i + 2]) * 26 + letters[i + 3]
        total += model[key]
    return total / (used - 3)


def verify():
    assert SAVED["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    alphabet = json.loads(pinned("data/index.json"))["alphabet"]
    index = {row["rune"]: i for i, row in enumerate(alphabet)}
    labels = [row["latin"] for row in alphabet]
    token_lengths = np.array([len(text) for text in labels], dtype=np.int64)
    token_letters = np.zeros((29, 2), dtype=np.int64)
    for i, label in enumerate(labels):
        for j, letter in enumerate(label):
            token_letters[i, j] = ord(letter) - ord("A")
    lines = [x.split() for x in pinned("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
    normalizer = sum(int(n) for _, n in lines)
    model = np.full(26**4, math.log10(.01 / normalizer), dtype=np.float64)
    for gram, count in lines:
        slot = 0
        for letter in gram:
            slot = slot * 26 + ord(letter) - ord("A")
        model[slot] = math.log10(int(count) / normalizer)
    streams = []
    for name in PLAN["pages"]:
        page = json.loads(pinned(f"data/pages/{name}.json"))
        values = [index[ch] for ch in page["raw"] if ch in index]
        assert len(values) == page["rune_count"]
        streams.append(np.array(values, dtype=np.int64))
    assert json.loads(pinned("data/pages/lp2-50.json"))["rune_count"] == 0
    max_length = max(map(len, streams))
    shifts = np.array([[phi_coprime(i + offset) % 29 for i in range(max_length)]
                       for offset in range(PLAN["operator_count"])], dtype=np.int64)
    # Full original grid and independent per-page winners.
    original = np.array([[alternate_score(row, key, token_lengths, token_letters, model)
                          for key in shifts] for row in streams])
    assert original.shape == (55, 100)
    for i, saved in enumerate(SAVED["pages"]):
        winner = int(np.argmax(original[i]))
        assert saved["page"] == PLAN["pages"][i] and saved["best_offset"] == winner
        assert abs(saved["best_score"] - original[i, winner]) < 1e-11
        decoded = [(int(v) - int(shifts[winner, j])) % 29 for j, v in enumerate(streams[i])]
        assert saved["best_latin"] == "".join(labels[v] for v in decoded)
    global_winner = np.unravel_index(np.argmax(original), original.shape)
    assert SAVED["best"]["page"] == PLAN["pages"][global_winner[0]]
    assert SAVED["best"]["offset"] == global_winner[1]
    assert abs(SAVED["best"]["score"] - original[global_winner]) < 1e-11
    # Re-run the complete selection on every null replicate, not only the winner.
    maxima = []
    for rep in range(PLAN["control_replicates"]):
        best = -1e100
        for page_index, original_row in enumerate(streams):
            row = original_row.tolist()
            random.Random(PLAN["control_seed"] + 10000 * rep + page_index).shuffle(row)
            candidate = np.array(row, dtype=np.int64)
            for key in shifts:
                best = max(best, alternate_score(candidate, key, token_lengths, token_letters, model))
        maxima.append(best)
    assert len(maxima) == len(SAVED["null_maxima"]) == 199
    assert all(abs(a - b) < 1e-11 for a, b in zip(maxima, SAVED["null_maxima"]))
    assert SAVED["null_at_least_actual"] == sum(x >= SAVED["best"]["score"] for x in maxima)
    assert SAVED["selection_tail_plus_one"] == (SAVED["null_at_least_actual"] + 1) / 200
    # Distinct synthetic plaintext checks include the exact source sign and clock.
    for length, offset in [(66, 0), (85, 17), (184, 99)]:
        plain = [j * 7 % 29 for j in range(length)]
        cipher = [(v + phi_coprime(i + offset)) % 29 for i, v in enumerate(plain)]
        assert [(v - phi_coprime(i + offset)) % 29 for i, v in enumerate(cipher)] == plain
    assert SAVED["controls"]["recognized_readings"] == 9
    assert SAVED["controls"]["top_rank_plants"] == 9
    print("Independent coprime totients, all 5,500 outputs, 199 full null searches and plants pass")


if __name__ == "__main__":
    verify()
