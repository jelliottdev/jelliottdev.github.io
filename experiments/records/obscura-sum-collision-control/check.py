"""Independent page-record recount of OBSCURA target-sum collisions."""
from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
source = json.loads((ROOT / "experiments/records/mixed-square-word-sums/results.json").read_text(encoding="utf-8"))
target = {sum_value for _, sum_value in source["scope"]["candidates"]}
assert len(target) == len(result["distinct_sums"]) == 13
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
values = {row["rune"]: row["prime"] for row in alphabet}
counts = Counter()
words = 0
for n in range(56):
    page = json.loads((ROOT / "data/pages" / f"lp2-{n:02d}.json").read_text(encoding="utf-8"))
    runes = sum(c in values for c in page["raw"])
    assert runes == page["rune_count"]
    for token in re.split(r"[-.]", page["raw"]):
        total = sum(values[c] for c in token if c in values)
        if total:
            words += 1
            counts[total] += total in target
assert words == result["word_count"] == 2928
assert {str(n): counts[n] for n in sorted(target)} == result["observed_by_sum"]
assert sum(counts.values()) == result["observed_total"] == 104
null = result["null_counts"]
assert len(null) == result["null"]["trials"] == 2000
assert sum(n >= 104 for n in null) == result["null"]["at_least_observed"]
assert min(null) >= 0 and max(null) <= words
print("Independently checked 104 matching word sums in 2,928 words")
