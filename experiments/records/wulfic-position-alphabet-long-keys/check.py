"""Independently check Stage W's complete control and verdict bookkeeping."""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NAMES = ("hint raw", "hint-reversed raw", "page_17.bin raw", "page_21.bin raw", "page_43.bin raw")
ALIGNMENTS = tuple(str(x) for x in range(7, 16)) + ("7-15",)
THRESHOLD = 30.0


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]

    stage_s = rows("source-stage_s_dependency.tsv")
    controls = rows("source-stage_w_controls.tsv")
    candidates = rows("source-stage_w_candidates.tsv")
    assert len(stage_s) == 50 and len(controls) == 505 and len(candidates) == 50
    assert {(r["key"], r["segment"]) for r in stage_s} == {
        (name, alignment) for name in NAMES for alignment in ALIGNMENTS}
    assert {(r["key"], r["alignment"]) for r in candidates} == {
        (name, alignment) for name in NAMES for alignment in ALIGNMENTS}
    for row in stage_s:
        assert row["alignment"] == ("continuous" if row["segment"] == "7-15" else "per-section")
        assert 0 <= int(row["best_phase"]) < int(row["phases"])
        assert float(row["log_mean_lr"]) <= float(row["best_phase_log_lr"]) + 0.005
    assert Counter(r["kind"] for r in controls) == {
        "positive": 250, "flat-negative": 250, "lp2-null": 5}
    dependency = {(r["key"], r["segment"]): r for r in stage_s}
    summary = Counter()
    for row in candidates:
        key, alignment = row["key"], row["alignment"]
        assert key in NAMES and alignment in ALIGNMENTS
        earlier = dependency[(key, alignment)]
        assert earlier["runes"] == row["runes"] and earlier["phases"] == row["phases"]
        assert earlier["best_phase"] == row["best_phase"]
        assert 0 <= int(row["best_phase"]) < int(row["phases"])
        assert float(row["log_mean_lr"]) <= float(row["best_phase_log_lr"]) + 0.005
        assert abs(float(row["log_mean_lr"]) - float(earlier["log_mean_lr"])) <= 0.005
        assert abs(float(row["best_phase_log_lr"]) - float(earlier["best_phase_log_lr"])) <= 0.005
        own = [r for r in controls if r["key"] == key and r["alignment"] == alignment
               and r["kind"] in ("positive", "flat-negative")]
        assert Counter(r["kind"] for r in own) == {"positive": 5, "flat-negative": 5}
        assert {int(r["seed"]) for r in own if r["kind"] == "positive"} == set(range(5))
        assert {int(r["seed"]) for r in own if r["kind"] == "flat-negative"} == set(range(5))
        assert all(int(r["runes"]) == int(row["runes"]) for r in own)
        positives = [float(r["log_mean_lr"]) for r in own if r["kind"] == "positive"]
        value = float(row["log_mean_lr"])
        verdict = ("PASS" if value >= THRESHOLD else
                   "EXCLUDED" if min(positives) >= THRESHOLD else "untestable")
        assert row["verdict"] == verdict, (key, alignment)
        summary[verdict] += 1
    nulls = [r for r in controls if r["kind"] == "lp2-null"]
    assert {r["key"] for r in nulls} == set(NAMES)
    assert all(r["alignment"] == "7-15" for r in nulls)
    negatives = [float(r["log_mean_lr"]) for r in controls if r["kind"] != "positive"]
    assert result["void"] == any(score >= THRESHOLD for score in negatives)
    assert result["verdict_counts"] == {kind: summary[kind] for kind in ("PASS", "EXCLUDED", "untestable")}
    assert abs(result["worst_negative"] - max(negatives)) < 0.005
    print("Stage S dependency, 505 controls, 50 LP2 cells and all source verdicts: OK")


if __name__ == "__main__":
    check()
