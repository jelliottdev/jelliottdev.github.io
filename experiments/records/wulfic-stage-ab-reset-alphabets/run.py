"""Recompute Stage AB's observed statistic from the pinned, derived rune layout.

The original Monte Carlo source run is preserved in source-*.tsv. See
replay_source.py for a byte-checked replay of that upstream code and input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
TYPES = ("segment", "paragraph", "clause", "line", "page")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed(runes: list[int], lengths: list[int]) -> int:
    assert sum(lengths) == len(runes)
    counts: Counter[tuple[int, int]] = Counter()
    offset = 0
    for length in lengths:
        for position, rune in enumerate(runes[offset:offset + length]):
            counts[position, rune] += 1
        offset += length
    return sum(count * (count - 1) // 2 for count in counts.values())


def analytic(lengths: list[int]) -> float:
    return sum((sum(size > pos for size in lengths) * (sum(size > pos for size in lengths) - 1)) // 2
               for pos in range(max(lengths))) / 29


def build() -> dict:
    layout = json.loads((HERE / "layout.json").read_text(encoding="utf-8"))
    assert layout["schema"] == "liberpedia-wulfic-stage-ab-layout-v1"
    runes, units = layout["runes"], layout["unit_lengths"]
    assert len(runes) == 12956 and set(runes) <= set(range(29))
    assert set(units) == set(TYPES)
    with (HERE / "source-stage_ab_results.tsv").open(encoding="utf-8", newline="") as f:
        source = list(csv.DictReader(f, delimiter="\t"))
    assert [row["unit"] for row in source] == list(TYPES)
    out = []
    for row in source:
        name = row["unit"]
        lengths = units[name]
        count = observed(runes, lengths)
        expectation = analytic(lengths)
        assert count == int(row["K_LP2"])
        assert len(lengths) == int(row["units"])
        assert abs(expectation - float(row["analytic_mean"])) < 0.001
        assert row["verdict"] == "EXCLUDED"
        out.append({
            "unit": name, "unit_count": len(lengths), "observed_pairs": count,
            "null_mean": float(row["null_mean"]), "null_max": int(row["null_max"]),
            "emerson_positive_lower": float(row["E_lower"]),
            "solved_positive_lower": float(row["L_lower"]),
            "analytic_flat_mean": round(expectation, 6),
            "source_verdict": row["verdict"],
        })
    return {
        "schema": "liberpedia-wulfic-stage-ab-results-v1",
        "source_commit": layout["source_commit"],
        "runes": len(runes), "pages": len(units["page"]),
        "source_results_sha256": digest(HERE / "source-stage_ab_results.tsv"),
        "source_controls_sha256": digest(HERE / "source-stage_ab_controls.tsv"),
        "rows": out,
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
        print("Stage AB observed counts and saved result: OK")
    else:
        path.write_text(rendered, encoding="utf-8", newline="\n")
