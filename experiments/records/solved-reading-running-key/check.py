"""Independent full-grid verifier for the solved-reading running-key result."""
import csv
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def indices(name):
    with (ROOT / f"exports/readings/{name}.csv").open(encoding="utf-8", newline="") as stream:
        return [int(row["output_index"]) for row in csv.DictReader(stream)]


def page_values(name, alphabet):
    return [alphabet[ch] for ch in (ROOT / f"text/{name}.txt").read_text(encoding="utf-8") if ch in alphabet]


def load_model():
    counts = {}
    for line in (ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt").read_text(encoding="ascii").splitlines():
        word, number = line.split()
        counts[word] = int(number)
    z = math.log10(sum(counts.values()))
    return {word: math.log10(number) - z for word, number in counts.items()}, math.log10(0.01) - z


def complete_score(cipher, key, start, direction, labels, frequencies, penalty):
    plaintext = []
    for position, symbol in enumerate(cipher):
        value = (symbol + direction * key[start + position]) % 29
        plaintext.append(labels[value])
    joined = "".join(plaintext)
    total = 0.0
    for position in range(0, len(joined) - 3):
        total += frequencies.get(joined[position:position + 4], penalty)
    return total / (len(joined) - 3)


def maximum(cipher, key, labels, frequencies, penalty):
    best = (-math.inf, None, None)
    count = 0
    for start in range(len(key) - len(cipher) + 1):
        for direction in (-1, 1):
            candidate = complete_score(cipher, key, start, direction, labels, frequencies, penalty)
            count += 1
            if candidate > best[0]:
                best = (candidate, start, direction)
    return best, count


def verify():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == result["plan_sha256"]
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    a = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
    lookup = {entry["rune"]: i for i, entry in enumerate(a)}
    labels = [entry["latin"] for entry in a]
    frequencies, penalty = load_model()
    sections = {part["id"]: indices(part["id"]) for part in plan["sections"]}
    key = [value for part in plan["sections"] for value in sections[part["id"]]]
    assert len(key) == 2892
    assert hashlib.sha256(bytes(key)).hexdigest() == result["source"]["indices_sha256"]
    controls = [part for part in plan["sections"] if part["id"] != plan["plant"]["held_out_key_section"]]
    plant_key = [value for part in controls for value in sections[part["id"]]]
    plant_start = sum(len(sections[p["id"]]) for p in controls[:next(i for i, p in enumerate(controls) if p["id"] == plan["plant"]["key_section"])]) + plan["plant"]["offset_in_section"]
    target = sections["warning"]
    cipher = [(value + plant_key[plant_start + i]) % 29 for i, value in enumerate(target)]
    plant_best, _ = maximum(cipher, plant_key, labels, frequencies, penalty)
    assert (plant_best[1], plant_best[2]) == (plant_start, -1)
    assert (plant_best[0], plant_start) == (result["plant"]["score"], result["plant"]["true_offset"])

    page_rows = [(name, page_values(name, lookup)) for name in plan["targets"]]
    observed = []
    for (name, cipher), saved in zip(page_rows, result["observed"]):
        winner, count = maximum(cipher, key, labels, frequencies, penalty)
        assert (name, len(cipher), count) == (saved["page"], saved["runes"], saved["evaluations"])
        assert (winner[1], winner[2]) == (saved["offset"], saved["sign"])
        assert math.isclose(winner[0], saved["score"], rel_tol=0, abs_tol=1e-12)
        observed.append(winner[0])
    assert max(observed) == result["observed_global_best"]["score"]
    for null in result["null_global_maxima"]:
        shuffled = key[:]
        random.Random(null["seed"]).shuffle(shuffled)
        assert hashlib.sha256(bytes(shuffled)).hexdigest() == null["key_sha256"]
        winner = (-math.inf, None, None, None)
        for name, cipher in page_rows:
            score_and_params, _ = maximum(cipher, shuffled, labels, frequencies, penalty)
            if score_and_params[0] > winner[0]:
                winner = (*score_and_params, name)
        assert (winner[1], winner[2], winner[3]) == (null["offset"], null["sign"], null["page"])
        assert math.isclose(winner[0], null["score"], rel_tol=0, abs_tol=1e-12)
    exceed = sum(n["score"] >= result["observed_global_best"]["score"] for n in result["null_global_maxima"])
    assert exceed == result["null_at_or_above_observed"]
    print("PASS: independently recomputed every full-page candidate and shared-key control maximum")


if __name__ == "__main__":
    verify()
