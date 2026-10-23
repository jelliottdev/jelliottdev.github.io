"""Independent reconstruction of every whole-page score and null maximum."""
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
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]
input_hashes = {row["path"]: row["sha256"] for row in plan["inputs"]}


def read(path):
    relative = path.relative_to(ROOT).as_posix()
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == input_hashes[relative]
    return data


alphabet = json.loads(read(ROOT / "data/index.json"))["alphabet"]
by_rune = {row["rune"]: number for number, row in enumerate(alphabet)}
labels = tuple(row["latin"] for row in alphabet)
source_plan = json.loads(read(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json"))
keyrows = {row["id"]: tuple(row["indices"]) for row in source_plan["keys"]}
assert list(keyrows) == plan["keys"]
model = [row.split() for row in read(ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt").decode("ascii").splitlines()]
total = sum(int(n) for _, n in model)
probabilities = {quad: math.log10(int(count) / total) for quad, count in model}
unseen = math.log10(0.01 / total)


def score(indices):
    letters = "".join(labels[value] for value in indices)
    return sum(probabilities.get(letters[start:start + 4], unseen) for start in range(len(letters) - 3)) / (len(letters) - 3)


settings = [(name, phase, sign, keyrows[name]) for name in plan["keys"]
            for phase in range(len(keyrows[name])) for sign in (-1, 1)]
assert len(settings) == 42


def plaintext(cipher, setting):
    name, phase, sign, key = setting
    length = len(key)
    return tuple((symbol + sign * key[(position + phase) % length]) % 29
                 for position, symbol in enumerate(cipher))


pages = []
for page_id in plan["pages"]:
    page = json.loads(read(ROOT / f"data/pages/{page_id}.json"))
    values = tuple(by_rune[symbol] for symbol in page["raw"] if symbol in by_rune)
    assert len(values) == page["rune_count"] and len(values) >= 66
    pages.append((page_id, values))
assert len(pages) == saved["page_count"] == 55
assert json.loads(read(ROOT / "data/pages/lp2-50.json"))["rune_count"] == 0

observed = []
for page_id, cipher in pages:
    for setting in settings:
        clear = plaintext(cipher, setting)
        observed.append((page_id, setting[0], setting[1], setting[2], len(clear), score(clear),
                         hashlib.sha256(bytes(clear)).hexdigest()))
observed.sort(key=lambda x: (-x[5], x[0], x[1], x[2], x[3]))
assert len(observed) == saved["case_count"] == 2310
for computed, archived in zip(observed, saved["cases"]):
    assert computed[:5] == (archived["page"], archived["key"], archived["phase"], archived["sign"], archived["runes"])
    assert math.isclose(computed[5], archived["score"], abs_tol=1e-11)
    assert computed[6] == archived["indices_sha256"]
assert math.isclose(observed[0][5], saved["best_score"], abs_tol=1e-11)
assert sum(row[5] >= plan["score_threshold"] for row in observed) == saved["threshold_passes"]

control_rows = []
for index, row in enumerate(saved["control_gate"]["rows"]):
    source = read(ROOT / f"exports/readings/{row['reading']}.csv").decode("utf-8-sig")
    clear = tuple(int(entry["output_index"]) for entry in csv.DictReader(source.splitlines()))[:66]
    assert len(clear) == 66
    direct = score(clear)
    assert math.isclose(direct, row["source_score"], abs_tol=1e-11)
    better = 0
    for rep in range(plan["control_replicates"]):
        shuffled = list(clear)
        random.Random(plan["control_seed"] + 1000 * index + rep).shuffle(shuffled)
        better += score(shuffled) < direct
    assert better == row["shuffles_below"]
    label = tuple(row["planted_setting"])
    original = next(setting for setting in settings if setting[:3] == label)
    key = original[3]
    planted = tuple((value - original[2] * key[(pos + original[1]) % len(key)]) % 29
                    for pos, value in enumerate(clear))
    assert plaintext(planted, original) == clear
    order = sorted(((score(plaintext(planted, setting)), setting[:3]) for setting in settings), reverse=True)
    rank = next(position + 1 for position, (_, candidate) in enumerate(order) if candidate == label)
    assert rank == row["planted_true_rank"]
    control_rows.append((direct >= plan["score_threshold"] and better >= 198, rank == 1))
assert sum(x[0] for x in control_rows) == saved["control_gate"]["good_originals"] == 9
assert sum(x[1] for x in control_rows) == saved["control_gate"]["top_rank_plants"] == 9
assert saved["control_gate"]["passed"]

nulls = []
for rep in range(plan["null_replicates"]):
    best = -math.inf
    for page_number, (_, cipher) in enumerate(pages):
        rearranged = list(cipher)
        random.Random(plan["null_seed"] + rep * 1000 + page_number).shuffle(rearranged)
        for setting in settings:
            best = max(best, score(plaintext(rearranged, setting)))
    nulls.append(best)
assert len(nulls) == len(saved["null_maxima"]) == 199
assert all(math.isclose(a, b, abs_tol=1e-11) for a, b in zip(nulls, saved["null_maxima"]))
assert sum(value >= observed[0][5] for value in nulls) == saved["null_at_least_best"]
assert math.isclose((1 + saved["null_at_least_best"]) / 200, saved["empirical_global_tail"], abs_tol=1e-12)
print("PASS: independent full-page, control and 199 complete-search null reconstruction")
