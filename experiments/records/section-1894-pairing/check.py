"""Independent section extraction and spot checks for the 1,894 pairing."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
order = {row["rune"]: int(row["index"]) for row in index["alphabet"]}


def source(name, part=None):
    raw = (ROOT / f"text/{name}.txt").read_text(encoding="utf-8")
    chunks = ["".join(c for c in chunk if "\u16a0" <= c <= "\u16ff") for chunk in raw.split("&")]
    chunks = [chunk for chunk in chunks if chunk]
    return "".join(chunks) if part is None else chunks[part]


a = "".join(source(f"lp1-{p:02}") for p in range(6, 16)) + source("lp1-16", 0)
b = source("lp2-15", 1) + "".join(source(f"lp2-{p:02}") for p in range(16, 23))
assert len(a.replace("ᚠ", "")) == len(b) == saved["length"] == 1894
a = [order[c] for c in a if c != "ᚠ"]
b = [order[c] for c in b]


def independent_score(shift, reversed_b, subtract):
    if reversed_b:
        reversed_source = b[::-1]
        moved = reversed_source[shift:] + reversed_source[:shift]
    else:
        moved = b[shift:] + b[:shift]
    transformed = [(y - x if subtract else y + x) % 29 for x, y in zip(a, moved)]
    return sum(transformed.count(symbol) * (transformed.count(symbol) - 1) for symbol in range(29))


for offset in (0, 1, 317, 941, 1893):
    result = max(independent_score(offset, rev, sub) for rev in (False, True) for sub in (False, True))
    assert result == saved["all_shift_best_scores"][offset]
assert saved["variants"] == {
    "add": independent_score(0, False, False),
    "subtract": independent_score(0, False, True),
    "reverse-add": independent_score(0, True, False),
    "reverse-subtract": independent_score(0, True, True),
}
assert saved["nonzero_shifts_at_least_observed"] == sum(
    value >= saved["observed_best"] for value in saved["all_shift_best_scores"][1:]
)
assert saved["conditional_fraction"] == "1411/1894"
print("PASS: independent section extraction, observed variants and sampled shifts")
