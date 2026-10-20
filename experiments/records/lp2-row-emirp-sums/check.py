"""Trial-division and arithmetic-digit-reversal audit, plus baseline comparison."""
import hashlib
import itertools
import json
from math import isqrt
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
baseline = json.loads((HERE.parent / "lp2-row-prime-sums/results.json").read_text(encoding="utf-8"))
baseline_plan = json.loads((HERE.parent / "lp2-row-prime-sums/plan.json").read_text(encoding="utf-8"))
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
assert result["plan_sha256"] == sha(HERE / "plan.json")
for item in plan["inputs"]:
    assert sha(ROOT / item["path"]) == item["sha256"]
for field in ["pages", "representation", "null", "seed", "shuffle_trials", "tail",
              "monte_carlo_p", "threshold", "stopping_rule"]:
    assert plan[field] == baseline_plan[field], field


def prime(number):
    return number >= 2 and all(number % d for d in range(2, isqrt(number) + 1))


def reverse(number):
    answer = 0
    while number:
        number, digit = divmod(number, 10)
        answer = answer * 10 + digit
    return answer


def emirp(number):
    return prime(number) and reverse(number) != number and prime(reverse(number))


controls = [0, 1, 11, 13, 17, 23, 101, 107]
expected = [False, False, False, True, True, False, False, True]
assert [emirp(n) for n in controls] == expected
assert reverse(1200) == 21
from run import is_emirp, sieve
assert [is_emirp(n, sieve(1000)) for n in controls] == expected

alphabet = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))["alphabet"]
values = {r["rune"]: r["prime"] for r in alphabet}
assert [p["page"] for p in result["observed"]] == plan["pages"] == result["null_page_order"]
sources = []
for page, old in zip(result["observed"], baseline["observed"]):
    assert page["page"] == old["page"]
    rows = []
    expected_rows = []
    text = (ROOT / "text" / (page["page"] + ".txt")).read_text(encoding="utf-8")
    for line, raw in enumerate(text.splitlines(), 1):
        row = [values[c] for c in raw if c in values]
        if row:
            total = sum(row)
            rows.append(row)
            expected_rows.append({"line": line, "runes": len(row), "sum": total,
                                  "reverse": reverse(total), "prime": prime(total),
                                  "emirp": emirp(total)})
    assert page["rows"] == expected_rows
    assert [{key: row[key] for key in ["line", "runes", "sum", "prime"]}
            for row in expected_rows] == old["rows"]
    sources.append(rows)
observed = sum(emirp(sum(row)) for rows in sources for row in rows)
assert observed == result["emirp_row_count"]
assert sum(len(rows) for rows in sources) == result["row_count"] == baseline["row_count"]
rng = random.Random(plan["seed"])
for trial in result["null_trials"][:3]:
    counts = []
    for rows in sources:
        flat = list(itertools.chain.from_iterable(rows))
        rng.shuffle(flat)
        iterator = iter(flat)
        counts.append(sum(emirp(sum(itertools.islice(iterator, len(row)))) for row in rows))
        assert list(iterator) == []
    assert counts == trial["page_counts"]
assert len(result["null_trials"]) == len(baseline["null_trials"]) == plan["shuffle_trials"]
for number, (trial, old) in enumerate(zip(result["null_trials"], baseline["null_trials"]), 1):
    assert trial["trial"] == old["trial"] == number
    assert trial["prime_page_counts"] == old["page_counts"]
    assert len(trial["page_counts"]) == len(sources)
    for count, prime_count, rows in zip(trial["page_counts"], trial["prime_page_counts"], sources):
        assert type(count) is int and 0 <= count <= prime_count <= len(rows)
    assert trial["total"] == sum(trial["page_counts"])
    assert trial["at_least_observed"] == (trial["total"] >= observed)
exceed = sum(t["at_least_observed"] for t in result["null_trials"])
assert exceed == result["exceedances"]
assert result["monte_carlo_p"] == (exceed + 1) / (plan["shuffle_trials"] + 1)
assert result["threshold"] == plan["threshold"]
assert result["below_threshold"] == (result["monte_carlo_p"] < plan["threshold"])
print("All observed classifications, first three independent null counts, all tail records and 999 baseline prime-count vectors pass.")
