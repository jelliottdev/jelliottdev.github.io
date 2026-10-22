"""Independent source-coordinate, output and score checks for the paired streams."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "experiments/records/spiral-branches-paired-subtraction"
plan = json.loads((BASE / "plan.json").read_text(encoding="utf-8"))
results = json.loads((BASE / "results.json").read_text(encoding="utf-8"))
stream_bytes = (BASE / "candidate-streams.json").read_bytes()
streams = json.loads(stream_bytes)
assert hashlib.sha256(stream_bytes).hexdigest() == results["candidate_streams_sha256"]
assert hashlib.sha256((BASE / "plan.json").read_bytes()).hexdigest() == results["plan_sha256"]
index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
to_index = {row["rune"]: row["index"] for row in index["alphabet"]}
to_rune = {value: rune for rune, value in to_index.items()}
page_cache = {}


def page_values(page):
    if page not in page_cache:
        raw = (ROOT / f"text/{page}.txt").read_text(encoding="utf-8")
        page_cache[page] = [to_index[c] for c in raw if c in to_index]
    return page_cache[page]


def oracle_score(values):
    # Directly compare every unordered pair; the producer uses a frequency
    # table. For 2,883 positions this is 4,154,403 comparisons per variant.
    equal = 0
    for i, left in enumerate(values):
        equal += sum(left == right for right in values[i + 1:])
    return 2 * equal


b_rows = streams["b_without_f"]
b = [row["value"] for row in b_rows]
assert len(b) == 2883 and all(value != 0 for value in b)
for row in b_rows:
    assert page_values(row["page"])[row["page_rune_ordinal_zero_based"]] == row["value"]

direct_positions = None
variant_values = {}
for name in plan["variants"]:
    row = streams["variants"][name]
    a_rows = row["a"]
    positions = Counter((item["page"], item["page_rune_ordinal_zero_based"]) for item in a_rows)
    if direct_positions is None:
        direct_positions = positions
    else:
        assert positions == direct_positions
    assert len(a_rows) == len(b)
    a = [item["value"] for item in a_rows]
    for item in a_rows:
        source = page_values(item["page"])[item["page_rune_ordinal_zero_based"]]
        is_branch = item["page"] in {f"lp2-{i:02}" for i in range(8, 15)}
        is_title = item["page"] == "lp2-15"
        flipped = (name == "atbash-branches" and is_branch) or (name == "atbash-tail" and (is_branch or is_title))
        assert item["value"] == (28 - source if flipped else source)
    output = [(left - right) % 29 for left, right in zip(b, a)]
    assert "".join(to_rune[value] for value in output) == row["output_runes"]
    assert all((output[i] + a[i]) % 29 == b[i] for i in range(len(b)))
    assert oracle_score(output) == results["observed_pair_counts"][name]
    variant_values[name] = a

assert max(results["observed_pair_counts"].values()) == results["observed_max_pair_count"]
shifted = results["controls"]["nonzero_circular_shifts"]
assert len(shifted["maxima"]) == len(b) - 1
for offset in (1, len(b) // 2, len(b) - 1):
    rotated = b[offset:] + b[:offset]
    scores = [sum(n * (n - 1) for n in Counter((value - a[i]) % 29 for i, value in enumerate(rotated)).values())
              for a in variant_values.values()]
    assert max(scores) == shifted["maxima"][offset - 1]

shuffled = results["controls"]["within_page_shuffle"]
assert len(shuffled["maxima"]) == plan["shuffle_trials"]
chunks = []
for number in range(40, 54):
    chunks.append([item["value"] for item in b_rows if item["page"] == f"lp2-{number:02}"])
rng = random.Random(plan["shuffle_seed"])
trial = []
for chunk in chunks:
    copy = list(chunk)
    rng.shuffle(copy)
    trial.extend(copy)
first_max = max(sum(n * (n - 1) for n in Counter((value - a[i]) % 29 for i, value in enumerate(trial)).values())
                for a in variant_values.values())
assert first_max == shuffled["maxima"][0]
for item, denominator in [(shifted, len(b)), (shuffled, plan["shuffle_trials"] + 1)]:
    tail = sum(score >= results["observed_max_pair_count"] for score in item["maxima"])
    assert tail == item["tail_count"]
    assert item["comparison_fraction"] == f"{tail + 1}/{denominator}"
print("PASS: all source coordinates, five outputs and pairwise scores; sampled controls and complete tails")
