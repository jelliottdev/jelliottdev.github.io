"""Independent grid-byte reconstruction and Stage X2 row checks."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
CLASSES = ("EN", "RUNES", "HEX", "B64")


def grid_bytes() -> list[int]:
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as stream:
        tokens = [row["token"] for row in csv.DictReader(stream)]
    assert len(tokens) == 256 and all(len(token) == 2 for token in tokens)
    return [60 * DIGITS.index(token[0]) + DIGITS.index(token[1]) for token in tokens]


def column_major(values: list[int]) -> list[int]:
    assert len(values) == 256
    return [values[8 * row + col] for col in range(8) for row in range(32)]


def coincidences(values: list[int], period: int) -> int:
    """Count equal-value pairs in positions with identical residues modulo period."""
    assert len(values) == 256 and 1 <= period <= 128
    total = 0
    for residue in range(period):
        counts = Counter(values[residue::period])
        total += sum(count * (count - 1) // 2 for count in counts.values())
    return total


def pair_capacity(period: int) -> int:
    return sum((len(range(residue, 256, period)) *
                (len(range(residue, 256, period)) - 1)) // 2 for residue in range(period))


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]

    grid = grid_bytes()
    readings = {"R": grid, "C": column_major(grid)}
    rows = list(csv.DictReader((HERE / "source-stage_x_periodic.tsv").open(
        encoding="utf-8", newline=""), delimiter="\t"))
    assert len(rows) == 256
    assert [(r["reading"], int(r["period"])) for r in rows] == [
        (reading, period) for reading in ("R", "C") for period in range(1, 129)]
    for row in rows:
        reading, period = row["reading"], int(row["period"])
        observed = coincidences(readings[reading], period)
        assert observed == int(row["coincidences"]), (reading, period)
        assert pair_capacity(period) == int(row["pairs"])
        null_max = int(row["null_max"])
        assert row["structure"] == ("PASS" if observed > null_max else "-")
        assert 0 <= float(row["null_p_ge"]) <= 1
        for cls in CLASSES:
            cutoff = float(row[f"q001_{cls}"])
            assert row[f"verdict_{cls}"] == ("EXCLUDED" if observed < cutoff else "not excluded")

    # Post-replay mathematical control: residue-specific permutations conserve
    # every same-residue equality, including cases with repeated values.
    for period in (1, 7, 29, 128):
        plain = [(i // period) % 13 for i in range(256)]
        cipher = [(37 * plain[i] + 19 * (i % period)) % 256 for i in range(256)]
        assert coincidences(plain, period) == coincidences(cipher, period)
    print("Grid reconstruction, 256 full source rows, thresholds and planted bijections: OK")


if __name__ == "__main__":
    check()
