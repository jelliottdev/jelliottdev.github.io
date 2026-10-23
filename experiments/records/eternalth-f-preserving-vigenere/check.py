"""Independent exhaustive image and scoring check; does not import run.py."""
import csv
import hashlib
import json
import math
from pathlib import Path
import random


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan_bytes = (HERE / "plan.json").read_bytes()
plan = json.loads(plan_bytes)
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
assert report["plan_sha256"] == hashlib.sha256(plan_bytes).hexdigest()
input_hashes = {row["path"]: row["sha256"] for row in plan["inputs"]}


def read(relative):
    raw = (ROOT / relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == input_hashes[relative], relative
    return raw


alphabet = json.loads(read("data/index.json"))["alphabet"]
rune_to_latin = {row["rune"]: row["latin"] for row in alphabet}
index_to_latin = [row["latin"] for row in alphabet]
key = [ord(char) - ord("A") for char in plan["key"]]
letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def source_output(letter, slot, preserve_f):
    if preserve_f and letter == "F":
        return letter
    return letters[(letters.index(letter) + key[slot % len(key)]) % 26]


def direct_score(text, weights, floor):
    grams = (text[i:i + 4] for i in range(len(text) - 3))
    return sum(weights.get(gram, floor) for gram in grams) / (len(text) - 3)


fixture = plan["source_parity_fixture"]
assert "".join(source_output(c, i, False) for i, c in enumerate(fixture["input"])) == fixture["ordinary_plus"]
assert "".join(source_output(c, i, True) for i, c in enumerate(fixture["input"])) == fixture["f_preserving_plus"]
parity = json.loads((HERE / "source-parity.json").read_text(encoding="utf-8"))
assert parity["revision"] == plan["source"]["revision"]
assert parity["source_sha256"] == plan["source"]["sha256"]
assert parity["source_path"] == plan["source"]["path"]
for row in parity["fixtures"]:
    assert "".join(source_output(c, i, False) for i, c in enumerate(row["input"])) == row["ordinary_plus"]
    assert "".join(source_output(c, i, True) for i, c in enumerate(row["input"])) == row["f_preserving_plus"]
assert {"".join(source_output(c, i, True) for i, c in enumerate(text))
        for text in plan["collision_control"]["inputs"]} == {plan["collision_control"]["f_preserving_plus"]}

# Derive the image of each key slot by enumerating the entire A-Z source alphabet.
images = [{source_output(letter, slot, True) for letter in letters} for slot in range(11)]
for slot, row in enumerate(report["control_gate"]["slots"]):
    missing = sorted(set(letters) - images[slot])
    assert len(missing) == (0 if key[slot] == 0 else 1)
    assert row["image_size"] == len(images[slot]) and row["forbidden"] == (missing[0] if missing else None)

model_lines = read("experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()
counts = {gram: int(count) for gram, count in (line.split() for line in model_lines)}
denom = math.log10(sum(counts.values()))
weights = {gram: math.log10(count) - denom for gram, count in counts.items()}
floor = math.log10(0.01) - denom


def latin_of_runes(indices):
    return "".join(index_to_latin[value] for value in indices)


def inverse_ordinary(text):
    # Compute the preimage by a lookup for each slot instead of using modular subtraction.
    inverses = [{source_output(letter, slot, False): letter for letter in letters} for slot in range(11)]
    assert all(len(row) == 26 for row in inverses)
    return "".join(inverses[i % 11][char] for i, char in enumerate(text))


control = plan["english_controls"]
good = 0
for number, name in enumerate(plan["readings"]):
    rows = csv.DictReader(read(f"exports/readings/{name}.csv").decode("utf-8-sig").splitlines())
    indices = [int(row["output_index"]) for row in rows][:control["length_runes"]]
    assert len(indices) == control["length_runes"]
    plain = latin_of_runes(indices)
    planted = "".join(source_output(char, i, False) for i, char in enumerate(plain))
    assert inverse_ordinary(planted) == plain
    direct = direct_score(plain, weights, floor)
    below = 0
    for rep in range(control["shuffle_replicates_per_reading"]):
        shuffled = indices.copy()
        random.Random(control["shuffle_seed"] + 1000 * number + rep).shuffle(shuffled)
        below += direct_score(latin_of_runes(shuffled), weights, floor) < direct
    saved = report["control_gate"]["readings"][number]
    assert saved["reading"] == name and saved["latin_length"] == len(plain)
    assert abs(saved["source_score"] - direct) < 1e-12
    assert saved["shuffle_scores_below"] == below and saved["ordinary_plant_exact"]
    good += direct >= control["score_threshold"] and below >= 198
assert good == report["control_gate"]["good_originals"] == 9

pages = []
for page, saved in zip(plan["pages"], report["outcomes"]):
    data = json.loads(read(f"data/pages/{page}.json"))
    runes = [char for line in data["lines"] for char in line["raw"] if char in rune_to_latin]
    assert len(runes) == data["rune_count"]
    text = "".join(rune_to_latin[char] for char in runes)
    excluded = [i for i, char in enumerate(text) if char not in images[i % 11]]
    decoded = inverse_ordinary(text)
    actual_score = direct_score(decoded, weights, floor)
    assert saved["page"] == page and saved["runes"] == len(runes)
    assert saved["latin_characters"] == len(text)
    assert saved["f_forbidden_count"] == len(excluded)
    assert saved["f_first_forbidden_index"] == (excluded[0] if excluded else None)
    assert saved["f_image_possible"] == (not excluded)
    assert saved["ordinary_decoded_latin"] == decoded
    assert saved["ordinary_decoded_sha256"] == hashlib.sha256(decoded.encode("ascii")).hexdigest()
    assert abs(saved["ordinary_score"] - actual_score) < 1e-12
    pages.append((page, runes))
assert len(pages) == report["page_count"] == 55
assert json.loads(read("data/pages/lp2-50.json"))["rune_count"] == 0
assert [row["page"] for row in report["outcomes"] if row["f_image_possible"]] == report["f_possible_pages"]

nulls = []
for rep in range(plan["global_null"]["replicates"]):
    maximum = -math.inf
    for page_number, (_, runes) in enumerate(pages):
        shuffled = runes.copy()
        random.Random(plan["global_null"]["seed"] + 1000 * rep + page_number).shuffle(shuffled)
        text = "".join(rune_to_latin[char] for char in shuffled)
        maximum = max(maximum, direct_score(inverse_ordinary(text), weights, floor))
    nulls.append(maximum)
assert len(nulls) == len(report["null_maxima"])
assert all(abs(a - b) < 1e-12 for a, b in zip(nulls, report["null_maxima"]))
best = max(report["outcomes"], key=lambda row: row["ordinary_score"])
assert report["best_ordinary_page"] == best["page"]
assert report["best_ordinary_score"] == best["ordinary_score"]
assert report["ordinary_threshold_passes"] == sum(
    row["ordinary_score"] >= control["score_threshold"] for row in report["outcomes"])
tail = sum(x >= best["ordinary_score"] for x in nulls)
assert report["null_at_least_best"] == tail
assert report["empirical_global_tail"] == (tail + 1) / (len(nulls) + 1)
print("Independent source-image, controls, page outputs, and global null check passed")
