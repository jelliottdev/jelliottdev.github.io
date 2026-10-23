#!/usr/bin/env python3
"""Independent structural check of the pinned R26-C screen and its saved rows."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE / "source/liber-primus"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    seeds = json.loads((LP / "analysis/round26/C/seeds.json").read_text(encoding="utf-8"))["seeds"]
    rows = [json.loads(line) for line in (HERE / "rows.jsonl").open(encoding="utf-8")]
    assert len(seeds) == 323 and len(rows) == 4274
    expected = sum(6 if item["is_str"] else 14 for item in seeds)
    assert expected == len(rows)
    key = lambda row: (type(row["seed_value"]).__name__, row["seed_value"], row["generator"], row["preset"])
    assert len({key(row) for row in rows}) == len(rows)
    assert {row["preset"] for row in rows} == {"exact", "pair"}
    assert len({row["generator"] for row in rows}) == 7

    script = ast.parse((LP / "analysis/round26/C/sweep.py").read_text(encoding="utf-8"))
    assignments = [node for node in script.body if isinstance(node, ast.Assign)]
    bars = [ast.literal_eval(node.value) for node in assignments
            if any(isinstance(target, ast.Name) and target.id == "SCREEN_BAR" for target in node.targets)]
    assert bars == [5.0]
    gates = [node for node in ast.walk(script) if isinstance(node, ast.Compare)
             and isinstance(node.left, ast.Name) and node.left.id == "score"
             and len(node.ops) == 1 and isinstance(node.ops[0], ast.GtE)
             and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == "SCREEN_BAR"]
    assert len(gates) == 1

    qgrams = [line.split() for line in (LP / "data/english_quadgrams.txt").read_text(encoding="ascii").splitlines()]
    counts = [int(count) for _, count in qgrams]
    total = sum(counts)
    # Every known quadgram contributes log10(count / total) and an unseen
    # quadgram contributes log10(0.01 / total). Their averages cannot reach +5.
    highest_possible_term = math.log10(max(counts) / total)
    assert highest_possible_term < 0 and math.log10(0.01 / total) < 0
    scores = [row["screen_score"] for row in rows]
    assert max(scores) == saved["screen_score_max"] == -6.5781
    assert statistics.median(scores) == saved["screen_score_median"] == -7.347
    assert sum(s >= 5 for s in scores) == saved["screen_escalations"] == 0
    assert sha(HERE / "rows.jsonl") == saved["source_rows_sha256"]
    assert sha(LP / "analysis/round26/C/seeds.json") == saved["source_seeds_sha256"]
    assert saved["planted_screen"]["recovered"] == 120
    assert saved["planted_screen"]["screen_score"] < 0
    print(f"independent check passed: {len(rows):,} distinct rows; mathematical score ceiling {highest_possible_term:.4f} < +5")


if __name__ == "__main__":
    main()
