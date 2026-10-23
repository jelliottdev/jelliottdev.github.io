"""Verify the full Stage S replay without rehabilitating its void control gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
from collections import Counter
from pathlib import Path

PIN = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
THRESHOLD = 30.0


def rows(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8")), delimiter="\t"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    content = {}
    hashes = {}
    for name in ("stage_s_candidates.tsv", "stage_s_controls.tsv"):
        actual = (output / name).read_bytes()
        original = subprocess.check_output(
            ["git", "show", f"{PIN}:reference/findings/{name}"], cwd=source
        )
        if actual != original:
            raise AssertionError(f"{name} differs from pinned Git object")
        hashes[name] = hashlib.sha256(actual).hexdigest()
        content[name] = rows(actual)

    candidates = content["stage_s_candidates.tsv"]
    controls = content["stage_s_controls.tsv"]
    if len(candidates) != 200 or len(controls) != 260:
        raise AssertionError((len(candidates), len(controls)))
    names = {r["key"] for r in candidates}
    if len(names) != 20 or any(sum(r["key"] == n for r in candidates) != 10 for n in names):
        raise AssertionError("incomplete candidate grid")
    kinds = Counter(r["kind"] for r in controls)
    if kinds != {"positive": 120, "negative": 120, "lp2-null": 20}:
        raise AssertionError(kinds)
    all_scores = [float(r["log_mean_lr"]) for r in candidates]
    positives = [r for r in controls if r["kind"] == "positive"]
    negatives = [r for r in controls if r["kind"] != "positive"]
    void = [r for r in negatives if float(r["log_mean_lr"]) >= THRESHOLD]
    summary = {
        "source_commit": PIN,
        "stage": "S",
        "candidate_rows": len(candidates),
        "key_classings": len(names),
        "alignments_per_key": 10,
        "control_rows": len(controls),
        "control_kind_counts": dict(kinds),
        "sha256": hashes,
        "best_candidate_score": max(all_scores),
        "candidates_at_plus_30": sum(x >= THRESHOLD for x in all_scores),
        "min_positive_score": min(float(r["log_mean_lr"]) for r in positives),
        "max_negative_or_null_score": max(float(r["log_mean_lr"]) for r in negatives),
        "void_control_count": len(void),
        "void_controls": [
            {"key": r["key"], "kind": r["kind"], "runes": int(r["runes"]),
             "seed": int(r["seed"]), "score": float(r["log_mean_lr"])}
            for r in void
        ],
        "gate_valid": not void,
        "model_exclusions": 0 if void else None,
        "interpretation": "VOID gate forbids negative model exclusions" if void else "gate valid; review power by setting",
    }
    args.receipt.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"PASS exact source bytes: {len(candidates)} candidates, {len(controls)} controls; "
          f"void controls {len(void)}; best LP2 {summary['best_candidate_score']:+.2f}")


if __name__ == "__main__":
    main()
