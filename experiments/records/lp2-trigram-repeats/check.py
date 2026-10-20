"""Independent pairwise-window oracle for observed pages and three null trials.

Also audits all 999 stored score vectors and the Monte Carlo tail calculation.
The full run is separately repeated with run.py --check.
"""
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert result["plan_sha256"] == sha(HERE / "plan.json")
for item in plan["inputs"]:
    assert sha(ROOT / item["path"]) == item["sha256"]
alphabet = [r["rune"] for r in json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]]


def pairwise(stream):
    """Directly compare all distinct starting-position pairs; no count formula."""
    windows = [stream[i:i + 3] for i in range(max(0, len(stream) - 2))]
    return sum(windows[i] == windows[j]
               for i in range(len(windows)) for j in range(i + 1, len(windows)))


assert [pairwise(list(s)) for s in ["", "AB", "ABC", "AAAA", "AAAAA", "ABABA"]] == [0, 0, 0, 1, 3, 1]
from run import score
assert [score(list(s)) for s in ["", "AB", "ABC", "AAAA", "AAAAA", "ABABA"]] == [0, 0, 0, 1, 3, 1]

assert [p["page"] for p in result["observed"]] == plan["pages"] == result["null_page_order"]
streams = []
for page in result["observed"]:
    text = (ROOT / "text" / (page["page"] + ".txt")).read_text(encoding="utf-8")
    stream = [alphabet.index(c) for c in text if c in alphabet]
    streams.append(stream)
    assert page["rune_count"] == len(stream)
    assert page["window_count"] == max(0, len(stream) - 2)
    assert page["matching_pairs"] == pairwise(stream)
    windows = [tuple(stream[i:i + 3]) for i in range(max(0, len(stream) - 2))]
    expected = [
        {"indices": list(pattern), "starts": [i for i, w in enumerate(windows) if w == pattern]}
        for pattern in sorted(set(windows)) if windows.count(pattern) >= 2
    ]
    assert page["repeated_patterns"] == expected
observed = sum(p["matching_pairs"] for p in result["observed"])
assert observed == result["observed_total"]
rng = random.Random(plan["seed"])
for trial in result["null_trials"][:3]:
    scores = []
    for stream in streams:
        shuffled = stream.copy()
        rng.shuffle(shuffled)
        assert sorted(shuffled) == sorted(stream)
        scores.append(pairwise(shuffled))
    assert scores == trial["page_scores"]

assert len(result["null_trials"]) == plan["shuffle_trials"] == 999
for number, trial in enumerate(result["null_trials"], 1):
    assert trial["trial"] == number
    assert len(trial["page_scores"]) == len(streams)
    for stream, count in zip(streams, trial["page_scores"]):
        windows = max(0, len(stream) - 2)
        assert type(count) is int and 0 <= count <= windows * (windows - 1) // 2
    assert trial["total"] == sum(trial["page_scores"])
    assert trial["at_least_observed"] == (trial["total"] >= observed)
exceed = sum(trial["at_least_observed"] for trial in result["null_trials"])
assert exceed == result["exceedances"]
assert result["monte_carlo_p"] == (exceed + 1) / 1000
assert result["threshold"] == plan["threshold"]
assert result["below_threshold"] == (result["monte_carlo_p"] < plan["threshold"])
print("All observed repeat positions, pairwise controls, first three null trials and all 999 tail records pass.")
