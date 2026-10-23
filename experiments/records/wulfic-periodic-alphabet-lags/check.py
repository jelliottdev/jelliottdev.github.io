"""Independently reconstruct all 12,935 ciphertext-lag agreement counts."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def all_lags(stream: list[int]) -> list[int]:
    bits = [0] * 29
    for position, rune in enumerate(stream):
        bits[rune] |= 1 << position
    return [sum((mask & (mask >> lag)).bit_count() for mask in bits)
            for lag in range(11, len(stream) - 10)]


def lower_binomial(k: int, n: int, p: float) -> float:
    term = (1 - p) ** n
    total = term
    for i in range(k):
        term *= (n - i) * p / ((i + 1) * (1 - p))
        total += term
    return total


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    results = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert results["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    index = json.loads((ROOT / "data/index.json").read_text(encoding="utf-8"))
    alphabet = {entry["rune"]: entry["index"] for entry in index["alphabet"]}
    stream = []
    for page in range(56):
        raw = json.loads((ROOT / f"data/pages/lp2-{page:02d}.json").read_text(encoding="utf-8"))["raw"]
        stream.extend(alphabet[ch] for ch in raw if ch in alphabet)
    assert len(stream) == 12956
    counts = all_lags(stream)
    assert len(counts) == 12935
    with (HERE / "source-stage_ae_lags.tsv").open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    assert len(rows) == len(counts)
    for lag, (count, row) in enumerate(zip(counts, rows), 11):
        assert int(row["lag"]) == lag and int(row["pairs"]) == len(stream) - lag
        assert int(row["agreements"]) == count
        assert row["rate"] == f"{count / (len(stream) - lag):.5f}"
    assert Counter(row["verdict"] for row in rows) == {"EXCLUDED": 10030, "-": 2905}
    assert min(int(row["lag"]) for row in rows if row["verdict"] == "-") == 4908
    p0 = sum(value * value for value in Counter(stream).values()) / len(stream) ** 2
    assert abs(p0 - 0.034552920989091636) < 1e-12
    for period in (1033, 1729, 3301):
        row = rows[period - 11]
        n, k = int(row["pairs"]), int(row["agreements"])
        p_lower = lower_binomial(k, n, 0.05)
        assert math.isclose(p_lower, float(row["lower_p_model"]), rel_tol=0.001)
        assert p_lower <= math.exp(-10) and row["verdict"] == "EXCLUDED"
    with (HERE / "source-stage_ae_controls.tsv").open(encoding="utf-8", newline="") as source:
        controls = list(csv.DictReader(source, delimiter="\t"))
    assert len(controls) == 10 and all(int(row["draws"]) == 10 and int(row["excluded"]) == 0
                                       for row in controls)
    assert sum(int(row["passed"]) for row in controls) == results["control_passes"]
    # Any fixed bijective alphabet at each residue preserves equality at its period.
    plain = [((i * 3) ^ (i // 7)) % 29 for i in range(70)]
    period = 7
    cipher = [((1 + 2 * (i % period)) * x + 5 * (i % period)) % 29
              for i, x in enumerate(plain)]
    assert all((plain[i] == plain[i + period]) == (cipher[i] == cipher[i + period])
               for i in range(len(plain) - period))
    print("Independent all-lag bitset recount, named binomial tails and planted periodic alphabet: OK")


if __name__ == "__main__":
    check()
