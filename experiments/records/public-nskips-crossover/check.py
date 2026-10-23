"""Independently check the source L2 skip-count crossover and its exact scope."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE / "source/liber-primus"
LANE = Path("analysis/round21/L2-nskips-crossover-length")
LADDER = (400, 600, 900, 1200, 1600, 2400, 3600, 6000, 9000, 12956)


def load(root: Path, name: str) -> dict:
    return json.loads((root / LANE / name).read_text(encoding="utf-8"))


def crossover(rows: list[dict], mode: str, mech: str, register: str) -> int | None:
    selected = sorted((row for row in rows if row["mode"] == mode
                       and row["mech"] == mech and row["register"] == register),
                      key=lambda row: row["L"])
    for i, row in enumerate(selected):
        if row["separates"] and all(later["separates"] for later in selected[i:]):
            return row["L"]
    return None


def verify(root: Path = LP) -> dict:
    saved = load(root, "nskips_crossover.json")
    original = load(LP, "original_nskips_crossover.json")
    assert {k: v for k, v in saved.items() if k != "elapsed_s"} == {
        k: v for k, v in original.items() if k != "elapsed_s"}, "Source replay changed"
    assert saved["done"] and saved["seed"] == 3301
    assert saved["fpr"] == .01 and saved["null_M_per_L"] == 300
    assert tuple(saved["ladder"]) == LADDER

    rows = saved["points"]
    assert len(rows) == 34
    cells = {(row["L"], row["mode"], row["mech"], row["register"]) for row in rows}
    assert len(cells) == len(rows), "Duplicate measurement cells"
    assert Counter((row["mode"], row["mech"]) for row in rows) == {
        ("keyskip1", "keyskip"): 14, ("drift", "keyskip"): 10,
        ("keyskip1", "skip_by_two"): 10,
    }
    primary = [row for row in rows if row["register"] == "LP1_REAL"]
    for mode, mech in (("keyskip1", "keyskip"), ("drift", "keyskip"),
                       ("keyskip1", "skip_by_two")):
        assert {row["L"] for row in primary if row["mode"] == mode
                and row["mech"] == mech} == set(LADDER)

    # Recompute all reported descriptive values from each discrete histogram.
    nulls_by_length_mode: dict[tuple[int, str], tuple[tuple[int, int], ...]] = {}
    for row in rows:
        hist = {int(k): int(v) for k, v in row["null_hist"].items()}
        n = sum(hist.values())
        assert n == row["null_M"] == 300
        assert max(hist) == row["null_max"]
        assert round(sum(value * count for value, count in hist.items()) / n, 3) == row["null_mean"]
        q99 = next((value for value in sorted(hist)
                    if sum(count for item, count in hist.items() if item >= value) / n <= .01),
                   max(hist) + 1)
        assert q99 == row["null_q99"]
        observed = row["correct_nskips"]
        left = sum(count for value, count in hist.items() if value <= observed) / n
        right = sum(count for value, count in hist.items() if value >= observed) / n
        uncapped = 2 * min(left, right)  # preserve the source's threshold computation
        assert round(left, 4) == row["p_left"]
        assert round(right, 4) == row["p_right"]
        assert round(uncapped, 4) == row["p_two_sided"]
        assert row["separates"] == (uncapped <= .01 and row["recovery"] >= .90)
        key = row["L"], row["mode"]
        signature = tuple(sorted(hist.items()))
        if key in nulls_by_length_mode:
            assert nulls_by_length_mode[key] == signature, "Seeded null changed across panels"
        else:
            nulls_by_length_mode[key] = signature
    assert len(nulls_by_length_mode) == 20

    q1 = saved["q1_gate"]
    assert q1["L400"] == next(row for row in primary if row["L"] == 400
                               and row["mode"] == "keyskip1" and row["mech"] == "keyskip")
    assert q1["L12956"] == next(row for row in primary if row["L"] == 12956
                                 and row["mode"] == "keyskip1" and row["mech"] == "keyskip")
    assert q1["pass"] and not q1["L400"]["separates"]
    assert q1["L12956"]["separates"] and q1["L12956"]["recovery"] >= .99

    for mode, mech in (("keyskip1", "keyskip"), ("drift", "keyskip"),
                       ("keyskip1", "skip_by_two")):
        assert saved["crossover"][f"{mode}|{mech}"] == crossover(rows, mode, mech, "LP1_REAL")
    assert saved["crossover"] == {
        "keyskip1|keyskip": 6000,
        "drift|keyskip": 400,
        "keyskip1|skip_by_two": None,
    }
    for register, reported in saved["crossover_by_register"].items():
        assert reported == crossover(rows, "keyskip1", "keyskip", register)
    assert set(saved["crossover_by_register"]) == {
        "LP1_REAL", "LATIN", "OE", "EN_HALFVOWEL", "EN_MODERN"}
    assert {row["L"] for row in rows if row["register"] != "LP1_REAL"} == {6000}
    assert min(row["recovery"] for row in primary if row["mode"] == "keyskip1"
               and row["mech"] == "keyskip") >= .998
    assert max(row["recovery"] for row in primary if row["mech"] == "skip_by_two") < .90
    return {"cells": len(rows), "distinct_null_distributions": len(nulls_by_length_mode),
            "lengths": len(LADDER), "crossover_first_tested": 6000,
            "endpoint_gate_passed": True, "source_replay_matches": True}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
