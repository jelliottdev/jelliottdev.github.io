"""Independent token scanner and exact small-population null check."""
import itertools
import json
import random
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = set("ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ")
plan = json.loads((HERE / "plan.json").read_text())
result = json.loads((HERE / "results.json").read_text())
ledger = json.loads((HERE / "words.json").read_text(encoding="utf-8"))
lengths = []
for section in plan["sections"]:
    text = "".join((ROOT / f"text/{p}.txt").read_text(encoding="utf-8")
                   for p in section["pages"])
    text = "".join(c for c in text if c not in "/\r\n")
    tokens, current = [], ""
    for i, c in enumerate(text):
        if c in ALPHABET:
            current += c
        elif c == "'" and current and i + 1 < len(text) and text[i + 1] in ALPHABET:
            current += c
        elif current:
            tokens.append(current)
            current = ""
    if current:
        tokens.append(current)
    saved = [w for w in ledger if w["section"] == section["id"]]
    assert tokens == [w["ciphertext"] for w in saved]
    lengths.extend(sum(c in ALPHABET for c in token) for token in tokens)
assert lengths == [w["rune_length"] for w in ledger]
assert lengths == json.loads((HERE / "submitted-lengths.json").read_text())["lengths"]
assert len(lengths) == 464 and sum(lengths) == 1796
for i, word in enumerate(ledger):
    assert (word["word"], word["row"], word["column"]) == (i + 1, i // 16 + 1, i % 16 + 1)


def column_variance(values, k):
    means = [sum(Fraction(x) for x in values[j::k]) / (len(values) // k)
             for j in range(k)]
    mean = sum(means) / k
    return sum((x - mean) ** 2 for x in means) / k


def expectation(values, k):
    n = len(values)
    mean = Fraction(sum(values), n)
    population_variance = sum((x - mean) ** 2 for x in values) / n
    return population_variance * Fraction(k - 1, n - 1)


# Exact enumeration checks the finite-population expectation, including duplicates.
for toy in ([1, 2, 3, 4], [1, 1, 2, 4]):
    all_orders = list(itertools.permutations(toy))
    exact = sum(column_variance(order, 2) for order in all_orders) / len(all_orders)
    assert exact == expectation(toy, 2)
observed = column_variance(lengths, 16)
assert observed == Fraction(result["variance_of_column_means"])
assert expectation(lengths, 16) == Fraction(result["expected_variance"])
assert observed / expectation(lengths, 16) == Fraction(result["R_fraction"])
# Audit an initial sample of null trials by direct rational column means.
rng = random.Random(plan["seed"])
for score in result["null_integer_scores"][:32]:
    sample = lengths.copy()
    rng.shuffle(sample)
    assert column_variance(sample, 16) == Fraction(score, 16**3 * 29**2)
scores = result["null_integer_scores"]
assert len(scores) == plan["trials"]
assert sum(s <= result["observed_integer_score"] for s in scores) == result["lower_tail_with_ties"]
assert Fraction(result["lower_tail_with_ties"] + 1, len(scores) + 1) == Fraction(result["p_fraction"])
print("PASS: all 464 words; exact variance and null expectation; 32 null oracles; complete saved tail count")
