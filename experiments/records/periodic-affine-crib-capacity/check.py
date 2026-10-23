"""Algebraic independent oracle for the periodic-affine crib census."""
import csv
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
hashes = {item["path"]: item["sha256"] for item in plan["inputs"]}
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]


def pinned(path):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == hashes[path.relative_to(ROOT).as_posix()]
    return raw


def solve_slot(cipher, proposed, period, residue, modulus):
    positions = list(range(residue, len(proposed), period))
    first = positions[0]
    c0, p0 = cipher[first], proposed[first]
    slope = None
    for i in positions[1:]:
        dc = (cipher[i] - c0) % modulus
        dp = (proposed[i] - p0) % modulus
        if dc == 0:
            if dp != 0:
                return 0, c0, None
            continue
        required = dp * pow(dc, -1, modulus) % modulus
        if required == 0 or (slope is not None and required != slope):
            return 0, c0, None
        slope = required
    if slope is None:
        return modulus - 1, c0, None
    return 1, c0, (slope, (p0 - slope * c0) % modulus)


def infer(cipher, proposed, period, modulus):
    slots = [solve_slot(cipher, proposed, period, residue, modulus) for residue in range(period)]
    total = 1
    for count, _, _ in slots:
        total *= count
    if total == 0:
        return [slot[0] for slot in slots], 0, None
    forced = 0
    for i in range(len(proposed), min(len(cipher), 2 * len(proposed))):
        count, first_cipher, _ = slots[i % period]
        forced += (count == 1 or cipher[i] == first_cipher)
    return [slot[0] for slot in slots], total, forced


alphabet = json.loads(pinned(ROOT / "data/index.json"))["alphabet"]
lookup = {item["rune"]: index for index, item in enumerate(alphabet)}
known = json.loads(pinned(ROOT / "experiments/records/lp2-known-vigenere-keys/plan.json"))
openings = [(item["id"], tuple(item["indices"])) for item in known["openings"]]
assert len(openings) == saved["crib_count"] == 9
assert len(plan["pages"]) == saved["page_count"] == 55
index = 0
grouped = {str(period): {"impossible": 0, "unique": 0, "ambiguous": 0,
                         "compatible_key_max": 0, "forced_next12_sum": 0} for period in range(1, 9)}
for name in plan["pages"]:
    doc = json.loads(pinned(ROOT / f"data/pages/{name}.json"))
    cipher = tuple(lookup[r] for r in doc["raw"] if r in lookup)
    assert len(cipher) == doc["rune_count"] and len(cipher) >= 24
    for crib_id, proposed in openings:
        for period in range(1, 9):
            slot_counts, count, forced = infer(cipher[:24], proposed, period, 29)
            archived = saved["cases"][index]
            assert (archived["page"], archived["crib"], archived["period"]) == (name, crib_id, period)
            assert archived["slot_counts"] == slot_counts
            assert archived["compatible_keys"] == count
            assert archived["following_positions_forced"] == forced
            category = "impossible" if count == 0 else "unique" if count == 1 else "ambiguous"
            assert archived["status"] == category
            grouped[str(period)][category] += 1
            grouped[str(period)]["compatible_key_max"] = max(grouped[str(period)]["compatible_key_max"], count)
            if forced is not None:
                grouped[str(period)]["forced_next12_sum"] += forced
            index += 1
assert index == saved["case_count"] == 3960
assert grouped == saved["by_period"]
assert json.loads(pinned(ROOT / "data/pages/lp2-50.json"))["rune_count"] == 0

# Plant a known 3-phase cipher and verify both uniqueness and its 12-symbol continuation.
fixture = plan["planted_control"]
trace = pinned(ROOT / "exports/readings/warning.csv").decode("utf-8-sig")
plain = tuple(int(row["output_index"]) for row in csv.DictReader(trace.splitlines()))[:24]
maps = [(item["a"], item["b"]) for item in fixture["maps"]]
coded = tuple(pow(maps[i % 3][0], -1, 29) * (value - maps[i % 3][1]) % 29
              for i, value in enumerate(plain))
counts, count, forced = infer(coded, plain[:12], 3, 29)
assert counts == [1, 1, 1] and count == 1 and forced == 12
assert saved["planted_control"]["slot_counts"] == counts
assert saved["planted_control"]["compatible_keys"] == count
assert saved["planted_control"]["following_positions_forced"] == forced
for residue, (a, b) in enumerate(maps):
    assert solve_slot(coded, plain[:12], 3, residue, 29)[2] == (a, b)

# Exhaustive small-field oracle across all target words under several ciphertext structures.
toy_ciphertexts = ((0, 0, 0, 0, 0, 0), (0, 1, 2, 0, 2, 1), (0, 0, 2, 2, 1, 1))
small_keys = [(a, b) for a in (1, 2) for b in range(3)]
tested = 0
for cipher in toy_ciphertexts:
    for proposed in itertools.product(range(3), repeat=6):
        for period in (1, 2, 3):
            analytic = infer(cipher, proposed, period, 3)[1]
            brute = 0
            for key in itertools.product(small_keys, repeat=period):
                if all((key[i % period][0] * cipher[i] + key[i % period][1]) % 3 == proposed[i]
                       for i in range(6)):
                    brute += 1
            assert analytic == brute
            tested += 1
assert tested == saved["toy_control"]["exact_count_comparisons"] == 6561
assert saved["toy_control"]["passed"] and saved["planted_control"]["passed"]
print("PASS: algebraic page census and 6,561 exhaustive F3 count checks")
