"""Independent grid, control, duplicate-key and arithmetic-prefix audit."""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIBLING = HERE.parent / "wulfic-stage-ab-reset-alphabets"
SEGMENTS = tuple(map(str, range(7, 16))) + ("7-15",)
MODES = ("sub", "add", "beaufort")


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file, delimiter="\t"))


def small_arithmetic_prefixes() -> dict[str, list[int]]:
    phi, sigma = [], []
    for n in range(1, 6):
        phi.append(sum(1 for k in range(1, n + 1) if coprime(n, k)))
        sigma.append(sum(k for k in range(1, n + 1) if n % k == 0))
    primes = [2, 3, 5, 7, 11, 13]
    raw = {
        "totient": phi, "sigma": sigma,
        "totient-sum": [sum(phi[:n]) for n in range(1, 6)],
        "prime-gaps": [b - a for a, b in zip(primes, primes[1:])],
        "totient-of-totient": [phi[x - 1] for x in phi],
        "n-times-totient": [n * value for n, value in enumerate(phi, start=1)],
    }
    out = {}
    for name, values in raw.items():
        out[name + " raw"] = [value % 29 for value in values]
        acc, chain = 0, []
        for value in values:
            acc = (acc + value) % 29
            chain.append(acc)
        out[name + " chain"] = chain
    return out


def coprime(a: int, b: int) -> bool:
    while b:
        a, b = b, a % b
    return a == 1


def check() -> None:
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    layout = json.loads((SIBLING / "layout.json").read_text(encoding="utf-8"))
    lengths = layout["unit_lengths"]["segment"]
    assert len(lengths) == 9 and sum(lengths) == 12956
    spec = importlib.util.spec_from_file_location("stage_ab_site_reader", SIBLING / "check.py")
    assert spec and spec.loader
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)
    (site_runes, unit_ids) = site.manuscript()
    assert site_runes == layout["runes"]
    assert site.summarize(unit_ids["segment"])[0] == lengths
    assert plan["arithmetic_first_five"] == small_arithmetic_prefixes()
    total, passing = 0, 0
    for stage in report["stages"]:
        token = stage["stage"].lower()
        grid = rows(f"source-stage_{token}_candidates.tsv")
        controls = rows(f"source-stage_{token}_controls.tsv")
        names = {row["source"] for row in grid}
        assert len(names) == stage["source_count"]
        expected_cells = {(name, segment, mode, offset) for name in names
                          for segment in SEGMENTS for mode in MODES for offset in range(29)}
        actual_cells = {(row["source"], row["segment"], row["mode"], int(row["shift"])) for row in grid}
        assert expected_cells == actual_cells and len(grid) == len(actual_cells)
        by_cell: dict[tuple[str, str, str], list[float]] = defaultdict(list)
        for row in grid:
            segment = row["segment"]
            expected_length = 12956 if segment == "7-15" else lengths[int(segment) - 7]
            assert int(row["runes"]) == expected_length
            by_cell[row["source"], segment, row["mode"]].append(float(row["log_lr"]))
        assert sum(max(scores) <= -10 for scores in by_cell.values()) == stage["excluded_cells"]
        assert len(controls) == 4 * len(names)
        for name in names:
            subset = [row for row in controls if row["source"] == name]
            assert {(int(row["runes"]), row["rekey"]) for row in subset} == {
                (729, "fresh"), (729, "next"), (3316, "fresh"), (3316, "next")}
        assert all(float(row["positive_log_lr"]) >= 30 and float(row["negative_log_lr"]) < 30
                   for row in controls)
        source_best = max(float(row["log_lr"]) for row in grid)
        assert source_best == float(stage["best_any"]["log_lr"])
        total += len(grid)
        passing += sum(float(row["log_lr"]) >= 30 for row in grid)
        if stage["stage"] == "AH":
            # These two source labels generate the same key at every position.
            a = {(r["segment"], r["mode"], r["shift"]): r["log_lr"] for r in grid
                 if r["source"] == "totient chain"}
            b = {(r["segment"], r["mode"], r["shift"]): r["log_lr"] for r in grid
                 if r["source"] == "totient-sum raw"}
            assert len(a) == 870 and a == b
    assert total == report["total_candidate_rows"] == 19140
    assert passing == report["total_pass_rows"]
    print("Independent source grid, controls, sections and arithmetic-prefix checks: OK")


if __name__ == "__main__":
    check()
