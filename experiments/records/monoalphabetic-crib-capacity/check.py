"""Independent pair-set oracle for the frozen substitution crib census."""
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
hashes = {item["path"]: item["sha256"] for item in plan["inputs"]}
assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == saved["plan_sha256"]


def pinned(relative):
    raw = (ROOT / relative).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == hashes[relative]
    return raw


def independent_count(cipher, proposed, continuation, q):
    pairs = set(zip(cipher, proposed, strict=True))
    left = {c for c, _ in pairs}
    right = {p for _, p in pairs}
    valid = len(pairs) == len(left) == len(right)
    if not valid:
        return 0, "0", None
    return len(left), str(math.factorial(q - len(left))), sum(c in left for c in continuation)


alphabet = json.loads(pinned("data/index.json"))["alphabet"]
lookup = {item["rune"]: i for i, item in enumerate(alphabet)}
openings = json.loads(pinned("experiments/records/lp2-known-vigenere-keys/plan.json"))["openings"]
assert len(openings) == 9 and len(plan["pages"]) == 55
index = 0
fit = []
for page_id in plan["pages"]:
    page = json.loads(pinned(f"data/pages/{page_id}.json"))
    cipher = [lookup[r] for r in page["raw"] if r in lookup]
    assert len(cipher) == page["rune_count"] and len(cipher) >= 24
    for opening in openings:
        m, keys, forced = independent_count(cipher[:12], opening["indices"], cipher[12:24], 29)
        row = saved["cases"][index]
        assert (row["page"], row["crib"]) == (page_id, opening["id"])
        assert (row["assigned_symbols"], row["compatible_keys"], row["following_positions_forced"]) == (m, keys, forced)
        assert row["compatible"] == (keys != "0")
        if row["compatible"]:
            fit.append(row)
        index += 1
assert index == saved["case_count"] == 495
assert len(fit) == saved["compatible_count"]
assert 495 - len(fit) == saved["impossible_count"]
assert [min((r["assigned_symbols"] for r in fit), default=None), max((r["assigned_symbols"] for r in fit), default=None)] == saved["assigned_symbol_range"]
assert [min((r["following_positions_forced"] for r in fit), default=None), max((r["following_positions_forced"] for r in fit), default=None)] == saved["forced_next12_range"]
assert json.loads(pinned("data/pages/lp2-50.json"))["rune_count"] == 0

trace = pinned("exports/readings/warning.csv").decode("utf-8-sig")
plain = [int(row["output_index"]) for row in csv.DictReader(trace.splitlines())][:24]
assert len(plain) == 24
a, b = 7, 11
inverse = pow(a, -1, 29)
cipher = [inverse * (p - b) % 29 for p in plain]
m, keys, forced = independent_count(cipher[:12], plain[:12], cipher[12:], 29)
assert saved["control"]["planted"] == {"reading": "warning", "runes": 24, "assigned_symbols": m, "compatible_keys": keys, "following_positions_forced": forced}
assert all((a * c + b) % 29 == p for c, p in zip(cipher, plain))

tested = 0
for q, patterns in ((3, ((0, 0, 1, 2), (0, 1, 0, 1), (0, 1, 2, 0))),
                    (5, ((0, 1, 2, 3), (0, 0, 1, 2), (0, 1, 0, 1)))):
    perms = tuple(itertools.permutations(range(q)))
    for cipher in patterns:
        for plain in itertools.product(range(q), repeat=4):
            analytical = int(independent_count(cipher, plain, (), q)[1])
            brute = sum(tuple(key[c] for c in cipher) == plain for key in perms)
            assert analytical == brute
            tested += 1
assert tested == saved["control"]["toy_exhaustive_comparisons"]
assert saved["control"]["passed"]
print(f"PASS: {index} page/crib cases, {tested} exhaustive small-alphabet oracles, planted reading")
