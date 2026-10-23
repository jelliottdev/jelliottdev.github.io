"""Recompute Wulfic Stage AF's LP2 difference statistic on the pinned layout."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SIBLING = HERE.parent / "wulfic-stage-ab-reset-alphabets"
TYPES = ("segment", "paragraph", "clause", "line", "page")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(runes: list[int], sizes: list[int], max_gap: int = 300) -> int:
    """Group each unit by in-unit position and count repeated mod-29 differences."""
    assert sum(sizes) == len(runes)
    width = max(sizes)
    grid = np.full((len(sizes), width), -1, dtype=np.int16)
    offset = 0
    for row, length in enumerate(sizes):
        grid[row, :length] = runes[offset:offset + length]
        offset += length
    count = 0
    for gap in range(2, min(max_gap, width - 1) + 1):
        left, right = grid[:, :-gap], grid[:, gap:]
        present = (left >= 0) & (right >= 0)
        if not np.any(present):
            continue
        positions = np.broadcast_to(np.arange(width - gap, dtype=np.int64), left.shape)
        differences = (right[present].astype(np.int64) - left[present].astype(np.int64)) % 29
        counts = np.bincount(positions[present] * 29 + differences)
        count += int(np.sum(counts * (counts - 1) // 2))
    return count


def expectation(sizes: list[int]) -> float:
    total = 0
    for gap in range(2, min(300, max(sizes) - 1) + 1):
        for second in range(gap, max(sizes)):
            eligible = sum(length > second for length in sizes)
            total += eligible * (eligible - 1) // 2
    return total / 29


def build() -> dict:
    layout = json.loads((SIBLING / "layout.json").read_text(encoding="utf-8"))
    runes, units = layout["runes"], layout["unit_lengths"]
    assert len(runes) == 12956 and set(units) == set(TYPES)
    with (HERE / "source-stage_af_results.tsv").open(encoding="utf-8", newline="") as f:
        source = list(csv.DictReader(f, delimiter="\t"))
    assert [row["unit"] for row in source] == list(TYPES)
    rows = []
    for row in source:
        kind = row["unit"]
        observed = score(runes, units[kind])
        null_mean = float(row["null_mean"])
        expected = expectation(units[kind])
        assert observed == int(row["S_LP2"])
        assert len(units[kind]) == int(row["units"])
        assert abs(expected - float(row["analytic_mean"])) < 0.001
        assert row["verdict"] == "EXCLUDED"
        rows.append({
            "unit": kind, "unit_count": len(units[kind]), "observed_pairs": observed,
            "null_mean": null_mean, "null_max": int(row["null_max"]),
            "emerson_positive_lower": float(row["E_lower"]),
            "solved_positive_lower": float(row["L_lower"]),
            "analytic_flat_mean": round(expected, 6),
            "source_verdict": row["verdict"],
        })
    return {
        "schema": "liberpedia-wulfic-stage-af-results-v1",
        "source_commit": layout["source_commit"], "runes": len(runes), "pages": len(units["page"]),
        "gap_min": 2, "gap_max": 300,
        "source_results_sha256": digest(HERE / "source-stage_af_results.tsv"),
        "source_controls_sha256": digest(HERE / "source-stage_af_controls.tsv"),
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build()
    path = HERE / "results.json"
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        assert path.read_text(encoding="utf-8") == rendered
        print("Stage AF observed counts and saved result: OK")
    else:
        path.write_text(rendered, encoding="utf-8", newline="\n")
