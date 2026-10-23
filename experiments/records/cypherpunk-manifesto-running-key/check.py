"""Independently replay every pinned manifesto running-key search."""

from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.chunks = []

    def handle_data(self, data):
        self.chunks.append(data)


plan_data = (HERE / "plan.json").read_bytes()
plan = json.loads(plan_data)
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
assert saved["plan_sha256"] == sha(plan_data)
for row in plan["inputs"]:
    assert sha((ROOT / row["path"]).read_bytes()) == row["sha256"]

raw = (HERE / "source.html").read_bytes().decode("latin-1")
assert raw.count("Privacy is necessary") >= 1
start = raw.index("Privacy is necessary")
end = raw.index("Eric Hughes", raw.index("Onward.", start))
parser = Text()
parser.feed(raw[start:end])
letters = "".join(c for c in " ".join(parser.chunks).upper() if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")
assert len(letters) == plan["source_normalized_letters"]
assert sha(letters.encode("ascii")) == plan["source_normalized_sha256"]
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
labels = [row["latin"] for row in alphabet]
by_rune = {row["rune"]: i for i, row in enumerate(alphabet)}
keys = {"ascii-ordinal": ["ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(c) for c in letters]}
aliases = {"V": 1, "K": 5, "Z": 15, "Q": 5}
longest = sorted(((label, i) for i, label in enumerate(labels)), key=lambda item: -len(item[0]))
parsed = []
at = 0
while at < len(letters):
    choice = next(((label, i) for label, i in longest if letters.startswith(label, at)), None)
    if choice:
        parsed.append(choice[1])
        at += len(choice[0])
    else:
        parsed.append(aliases[letters[at]])
        at += 1
keys["gp-greedy"] = parsed
assert [{"variant": variant, "length": len(key), "sha256": sha(bytes(key))}
        for variant, key in keys.items()] == saved["source_keys"]

counts = dict(line.split() for line in
              (ROOT / "experiments/records/english-scorer-controls/english_quadgrams.txt")
              .read_text(encoding="ascii").splitlines())
total = sum(map(int, counts.values()))
logp = {word: math.log10(int(n) / total) for word, n in counts.items()}
floor = math.log10(0.01 / total)
assert saved["quadgram_count"] == len(counts)
assert saved["quadgram_total"] == total
assert abs(saved["score_floor"] - floor) < 1e-12


def measure(cipher, key, offset):
    plain = "".join(labels[(symbol - key[offset + i]) % 29]
                    for i, symbol in enumerate(cipher))
    grams = Counter(plain[i:i + 4] for i in range(len(plain) - 3))
    score = sum(n * logp.get(gram, floor) for gram, n in grams.items()) / (len(plain) - 3)
    return score, plain


def top(cipher, key, number):
    rows = []
    for offset in range(len(key) - len(cipher) + 1):
        value, output = measure(cipher, key, offset)
        rows.append((value, -offset, output))
    return sorted(rows, key=lambda item: item[:2], reverse=True)[:number]


known = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
welcome = next(row for row in known["controls"] if row["id"] == "welcome")
plain = next(row["rune_indices"] for row in welcome["decoded_pages"] if row["page"] == "lp1-04")
for control in saved["positive_control"]:
    assert control["page"] == "lp1-04" and control["runes"] == len(plain) == 264
    key = keys[control["variant"]]
    offset = control["offset_zero_based"]
    cipher = [(p + key[offset + i]) % 29 for i, p in enumerate(plain)]
    ranked = top(cipher, key, 5)
    assert -ranked[0][1] == offset and control["true_offset_selected_first"]
    assert abs(ranked[0][0] - control["known_plaintext_score"]) < 1e-12
    assert len(ranked) == len(control["search"]["top"])
    for actual, stored in zip(ranked, control["search"]["top"]):
        assert stored["offset_zero_based"] == -actual[1]
        assert abs(stored["score"] - actual[0]) < 1e-12
        assert stored["latin"] == actual[2]
        assert stored["latin_sha256"] == sha(actual[2].encode("ascii"))

assert len(saved["targets"]) == 6
for row in saved["targets"]:
    key = keys[row["variant"]]
    raw_page = (ROOT / "text" / (row["page"] + ".txt")).read_text(encoding="utf-8")
    cipher = [by_rune[c] for c in raw_page if c in by_rune]
    assert row["page_runes"] == len(cipher)
    assert row["offsets_searched"] == len(key) - len(cipher) + 1
    ranked = top(cipher, key, 5)
    for actual, stored in zip(ranked, row["original_top_five"]):
        assert stored["offset_zero_based"] == -actual[1]
        assert abs(stored["score"] - actual[0]) < 1e-12
        assert stored["latin"] == actual[2]
        assert stored["latin_sha256"] == sha(actual[2].encode("ascii"))
    controls = []
    assert len(row["shuffle_maxima"]) == 16
    for item in row["shuffle_maxima"]:
        seed = item["seed"]
        assert 330100 <= seed <= 330115
        copy = list(key)
        random.Random(seed).shuffle(copy)
        assert sha(bytes(copy)) == item["key_sha256"]
        maximum = top(cipher, copy, 1)[0]
        assert abs(maximum[0] - item["maximum"]) < 1e-12
        assert -maximum[1] == item["offset_zero_based"]
        controls.append(maximum[0])
    assert row["shuffles_at_least_as_high"] == sum(value >= ranked[0][0] for value in controls)

print("PASS: independent parser and counted-quadgram replay verifies both variants, all whole-page offsets, shuffled maxima, and planted controls")
