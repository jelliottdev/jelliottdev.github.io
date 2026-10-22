"""Independent source and finite-count checks for the EA-frequency control."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
readings = json.loads((ROOT / "data/evidence/known-readings.json").read_text(encoding="utf-8"))
alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
labels = [entry["latin"] for entry in alphabet]
lookup = {entry["rune"]: i for i, entry in enumerate(alphabet)}
page_rows = []
joins = []
for group in readings["controls"]:
    for page in group["decoded_pages"]:
        indices = page["rune_indices"]
        assert "".join(map(labels.__getitem__, indices)) == "".join(re.findall(r"[A-Z]+", page["literal_transliteration"]))
        words = re.findall(r"[A-Z]+", re.sub(r"[/\r\n]", "", page["literal_transliteration"]))
        joins.extend((page["page"], a, b) for a, b in zip(words, words[1:])
                     if a[-1:] == "E" and b[:1] == "A")
        page_rows.append((page["page"], len(indices)-1, sum(index == 28 for index in indices[1:])))
lp1 = [row for row in page_rows if row[0].startswith("lp1-")]
lp2 = [row for row in page_rows if row[0].startswith("lp2-")]
assert (sum(row[1] for row in lp1), sum(row[2] for row in lp1)) == (2782, 20)
assert (sum(row[1] for row in lp2), sum(row[2] for row in lp2)) == (178, 0)
assert len([join for join in joins if join[0].startswith("lp1-")]) == 11
assert len(report["latin_segmentation"]["lp1_cross_word_ea_merges"]) == 11

frequencies = Counter()
edges = 0
for number in range(56):
    raw = (ROOT / f"text/lp2-{number:02d}.txt").read_text(encoding="utf-8")
    runes = [match.group() for match in re.finditer(r"[\u16a0-\u16ff]", raw)]
    assert all(rune in lookup for rune in runes)
    values = list(map(lookup.__getitem__, runes))
    edges += max(0, len(values)-1)
    frequencies.update((right-left) % 29 for left, right in zip(values, values[1:]))
assert edges == 12901 and frequencies[0] == 86
assert [frequencies[i] for i in range(29)] == report["unsolved_lp2"]["difference_counts"]
observed = Fraction(sum(count*(count-1) for count in frequencies.values()), edges*(edges-1))
expected = Fraction(86*85, edges*(edges-1)) + Fraction((edges-86)*(edges-87), 28*edges*(edges-1))
assert str(observed) == report["unsolved_lp2"]["difference_ioc_fraction"]
assert str(expected) == report["nonzero_uniform_control"]["expected_ioc_fraction"]
print("PASS decoded EA events, cross-word controls and exact difference IoC")
