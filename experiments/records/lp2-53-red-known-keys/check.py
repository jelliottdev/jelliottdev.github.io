"""Independent reconstruction of the LP2-53 red-span key search and controls."""
import csv
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
controls = json.loads((HERE / "controls.json").read_text(encoding="utf-8"))


def verified(path, digest):
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, path
    return data


assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]
assert hashlib.sha256((HERE / "controls.json").read_bytes()).hexdigest() == saved["controls_sha256"]
verified(ROOT / "images/lp2-53.jpg", plan["source_image_sha256"])
page = json.loads(verified(ROOT / "data/pages/lp2-53.json", plan["source_page_json_sha256"]))
alphabet = json.loads(verified(ROOT / "data/index.json", plan["alphabet_sha256"]))["alphabet"]
lookup = {r["rune"]: i for i, r in enumerate(alphabet)}
roman = [r["latin"] for r in alphabet]
streams = [[lookup[c] for c in line["raw"] if c in lookup] for line in page["lines"]]
assert [len(s) for s in streams] == [22, 22, 20, 23, 23, 19, 24, 22, 4]
red = streams[5][-1:] + sum(streams[6:], [])
assert len(red) == 51 and red == saved["red_indices"]
assert sum(map(len, streams[:6])) - 1 == 128
raw = page["lines"][5]["raw"].split(".")[-1] + "".join(line["raw"] for line in page["lines"][6:])
lengths = [sum(c in lookup for c in token) for token in raw.replace("/", "").split("-")]
assert [n for n in lengths if n] == plan["word_lengths"] == saved["word_lengths"]

known = json.loads(verified(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json", plan["known_keys_plan_sha256"]))
keys = {entry["id"]: entry["indices"] for entry in known["keys"] if entry["id"] in plan["key_ids"]}
assert set(keys) == set(plan["key_ids"])
model_lines = verified(ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt", plan["quadgram_model_sha256"]).decode("ascii").splitlines()
counts = dict((g, int(n)) for g, n in (line.split() for line in model_lines))
normalizer = math.log10(sum(counts.values()))
weights = {g: math.log10(n) - normalizer for g, n in counts.items()}
floor = math.log10(0.01) - normalizer


def score(seq):
    text = "".join(roman[i] for i in seq)
    return sum(weights.get(text[i:i + 4], floor) for i in range(len(text) - 3)) / (len(text) - 3)


def decodings(cipher):
    for name, key in keys.items():
        for phase in range(len(key)):
            for sign in (-1, 1):
                decoded = [(value + sign * key[(pos + phase) % len(key)]) % 29 for pos, value in enumerate(cipher)]
                yield (name, phase, sign), decoded


rows = []
for label, out in decodings(red):
    rows.append((label, score(out), "".join(roman[i] for i in out), hashlib.sha256(bytes(out)).hexdigest()))
rows.sort(key=lambda row: (-row[1], row[0]))
assert len(rows) == saved["case_count"] == 42
for expected, observed in zip(rows, saved["cases"]):
    label, value, text, digest = expected
    assert (observed["key"], observed["phase"], observed["sign"]) == label
    assert abs(observed["score"] - value) < 1e-10
    assert observed["output"] == text and observed["output_indices_sha256"] == digest

maxima = []
for rep in range(999):
    data = red.copy()
    random.Random(plan["control_seed"] + 100000 + rep).shuffle(data)
    maxima.append(max(score(out) for _label, out in decodings(data)))
assert len(maxima) == len(saved["null_maxima"])
assert all(abs(a - b) < 1e-10 for a, b in zip(maxima, saved["null_maxima"]))
assert sum(x >= rows[0][1] for x in maxima) == saved["null_at_least_best"] == 460
assert abs(saved["empirical_family_tail_fraction"] - 461 / 1000) < 1e-12
assert sum(row[1] >= plan["score_threshold"] for row in rows) == saved["passing_fixed_threshold"] == 0

good = 0
plants = 0
for idx, (name, digest) in enumerate(plan["control_readings"]):
    source = [int(r["output_index"]) for r in csv.DictReader(verified(ROOT / f"exports/readings/{name}.csv", digest).decode("utf-8-sig").splitlines())][:51]
    assert len(source) == 51
    direct = score(source)
    randomized = []
    for rep in range(200):
        data = source.copy()
        random.Random(plan["control_seed"] + 1000 * idx + rep).shuffle(data)
        randomized.append(score(data))
    assert abs(direct - controls["rows"][idx]["source_score"]) < 1e-10
    below = sum(x < direct for x in randomized)
    assert below == controls["rows"][idx]["shuffles_below"]
    good += direct >= -5.5 and below >= 198
    key_name = plan["key_ids"][idx % 2]
    key = keys[key_name]
    phase = (7 * idx + 3) % len(key)
    sign = plan["signs"][idx % 2]
    cipher = [(value - sign * key[(pos + phase) % len(key)]) % 29 for pos, value in enumerate(source)]
    ranked = sorted(((label, score(out)) for label, out in decodings(cipher)), key=lambda row: (-row[1], row[0]))
    rank = next(i + 1 for i, (label, _score) in enumerate(ranked) if label == (key_name, phase, sign))
    assert rank == controls["rows"][idx]["planted_true_rank"]
    plants += rank == 1
assert good == controls["good_originals"] == 9
assert plants == controls["top_rank_plants"] == 9
assert controls["passed"]
print("Independent check: red span, 42 key settings, 999 family-wise shuffles, and nine planted controls agree.")
