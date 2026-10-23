"""Independent pure-Python Stage AF difference-count check and planted control."""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SIBLING = HERE.parent / "wulfic-stage-ab-reset-alphabets"


def load_manuscript():
    path = SIBLING / "check.py"
    spec = importlib.util.spec_from_file_location("stage_ab_site_checker", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.manuscript(), module.summarize


def brute(units: list[list[int]], max_gap: int = 300) -> int:
    """Count difference collisions using counters one lag at a time."""
    score = 0
    for gap in range(2, min(max_gap, max(map(len, units)) - 1) + 1):
        groups: Counter[tuple[int, int]] = Counter()
        for unit in units:
            for first in range(len(unit) - gap):
                groups[first, (unit[first + gap] - unit[first]) % 29] += 1
        score += sum(count * (count - 1) // 2 for count in groups.values())
    return score


def main() -> None:
    (runes, unit_ids), summarize = load_manuscript()
    layout = json.loads((SIBLING / "layout.json").read_text(encoding="utf-8"))
    report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert runes == layout["runes"] and len(runes) == 12956
    with (HERE / "source-stage_af_results.tsv").open(encoding="utf-8", newline="") as f:
        source = list(csv.DictReader(f, delimiter="\t"))
    with (HERE / "source-stage_af_controls.tsv").open(encoding="utf-8", newline="") as f:
        controls = list(csv.DictReader(f, delimiter="\t"))
    assert len(source) == 5 and len(controls) == 10
    for row, upstream in zip(report["rows"], source, strict=True):
        kind = row["unit"]
        lengths, _ = summarize(unit_ids[kind])
        assert lengths == layout["unit_lengths"][kind]
        units, offset = [], 0
        for size in lengths:
            units.append(runes[offset:offset + size])
            offset += size
        assert offset == len(runes)
        observed = brute(units)
        assert observed == row["observed_pairs"] == int(upstream["S_LP2"])
        assert observed < min(float(upstream["E_lower"]), float(upstream["L_lower"]))
        minima = [int(control["min"]) for control in controls if control["unit"] == kind]
        assert len(minima) == 2 and min(minima) > int(upstream["null_max"])
    # The unit-specific shift must cancel from within-unit differences.
    plain = [[1, 4, 8, 11], [8, 11, 15, 18], [1, 4, 8, 11]]
    key = [3, 2, 5, 7]
    offsets = [2, 18, 9]
    additive = [[(p + key[t] + offsets[u]) % 29 for t, p in enumerate(unit)]
                for u, unit in enumerate(plain)]
    beaufort = [[(key[t] + offsets[u] - p) % 29 for t, p in enumerate(unit)]
                for u, unit in enumerate(plain)]
    assert brute(plain, 3) == brute(additive, 3) == brute(beaufort, 3)
    assert brute(plain, 3) > 0
    print("Independent site reconstruction, all five difference counts and shift controls: OK")


if __name__ == "__main__":
    main()
