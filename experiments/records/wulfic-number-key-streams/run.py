"""Summarize pinned Wulfic Stage AG/AH candidate and control grids."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = {
    "AG": ("pi", "e", "phi", "sqrt2", "sqrt3", "ln2", "sqrt3301",
           "copeland-erdos", "champernowne", "prime-totients"),
    "AH": tuple(f"{name} {form}" for name in ("totient", "sigma", "totient-sum", "prime-gaps",
                                                "totient-of-totient", "n-times-totient")
                for form in ("raw", "chain")),
}
SEGMENTS = tuple(map(str, range(7, 16))) + ("7-15",)
MODES = ("sub", "add", "beaufort")
PASS = 30.0
EXCLUDE = -10.0


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def summarize_stage(stage: str, names: tuple[str, ...]) -> dict:
    lower = stage.lower()
    candidates = table(f"source-stage_{lower}_candidates.tsv")
    controls = table(f"source-stage_{lower}_controls.tsv")
    expected = len(names) * len(SEGMENTS) * len(MODES) * 29
    assert len(candidates) == expected and len(controls) == len(names) * 4
    expected_cells = {(name, segment, mode, shift) for name in names
                      for segment in SEGMENTS for mode in MODES for shift in range(29)}
    seen = {(row["source"], row["segment"], row["mode"], int(row["shift"])) for row in candidates}
    assert seen == expected_cells
    assert {row["source"] for row in controls} == set(names)
    assert all(float(row["positive_log_lr"]) >= PASS and float(row["negative_log_lr"]) < PASS
               for row in controls)
    assert all(row["alignment"] == ("continuous" if row["segment"] == "7-15" else "per-section")
               for row in candidates)
    grouped: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in candidates:
        grouped[row["source"], row["segment"], row["mode"]].append(float(row["log_lr"]))
    excluded = sum(max(scores) <= EXCLUDE for scores in grouped.values())
    best = max(candidates, key=lambda row: float(row["log_lr"]))
    substantial = max((row for row in candidates if int(row["runes"]) >= 100),
                      key=lambda row: float(row["log_lr"]))
    by_source = []
    for name in names:
        rows = [row for row in candidates if row["source"] == name]
        by_source.append({"source": name,
                          "max_log_lr": max(float(row["log_lr"]) for row in rows),
                          "max_at_least_100_runes": max(float(row["log_lr"]) for row in rows
                                                        if int(row["runes"]) >= 100),
                          "excluded_cells": sum(max(grouped[name, segment, mode]) <= EXCLUDE
                                                for segment in SEGMENTS for mode in MODES)})
    return {
        "stage": stage, "source_count": len(names), "candidate_rows": len(candidates),
        "keyed_cells": len(grouped), "pass_rows": sum(float(row["log_lr"]) >= PASS for row in candidates),
        "excluded_cells": excluded, "source_control_rows": len(controls),
        "positive_control_min": min(float(row["positive_log_lr"]) for row in controls),
        "negative_control_max": max(float(row["negative_log_lr"]) for row in controls),
        "best_any": {key: best[key] for key in ("source", "segment", "mode", "shift", "runes", "log_lr")},
        "best_at_least_100_runes": {key: substantial[key] for key in
                                     ("source", "segment", "mode", "shift", "runes", "log_lr")},
        "by_source": by_source,
        "candidate_sha256": sha(HERE / f"source-stage_{lower}_candidates.tsv"),
        "controls_sha256": sha(HERE / f"source-stage_{lower}_controls.tsv"),
    }


def build() -> dict:
    stages = [summarize_stage(stage, names) for stage, names in STAGES.items()]
    return {
        "schema": "liberpedia-wulfic-number-key-streams-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "source_commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
        "starts_per_setting": 1000, "modes": list(MODES), "alignments": list(SEGMENTS),
        "total_candidate_rows": sum(stage["candidate_rows"] for stage in stages),
        "total_source_control_rows": sum(stage["source_control_rows"] for stage in stages),
        "total_pass_rows": sum(stage["pass_rows"] for stage in stages),
        "stages": stages,
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
        print("Wulfic AG/AH number-stream grids and controls: OK")
    else:
        path.write_text(rendered, encoding="utf-8", newline="\n")
