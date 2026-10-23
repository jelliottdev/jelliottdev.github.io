"""Summarize exact source Stage I/M tables and supplemental fixed-length controls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
THRESHOLD = 30.0
KEY_LENGTHS = {
    "K-A primes": 25912, "K-C word sums": 726, "K-D plaintext values": 2901,
    "G-B bytes": 256, "G-5 5-bit groups": 409, "G-D base-60 digits": 512,
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def build() -> dict:
    control_rows = table("supplemental-controls.tsv")
    by_control: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in control_rows:
        by_control[row["source"]].append(row)
    stages = []
    total = passed = 0
    for stage in ("i", "m"):
        source = table(f"source-stage_{stage}_candidates.tsv")
        names = [name for name in KEY_LENGTHS if (name.startswith("K-") if stage == "i" else name.startswith("G-"))]
        assert {r["key"] for r in source} == set(names)
        assert len(source) == (2610 if stage == "i" else 3132)
        settings = []
        for name in names:
            rows = [r for r in source if r["key"] == name]
            best_any = max(rows, key=lambda r: float(r["log_lr_nats"]))
            best_long = max((r for r in rows if int(r["runes"]) >= 100),
                            key=lambda r: float(r["log_lr_nats"]))
            controls = by_control[name]
            assert len(controls) == 20 and {int(r["seed"]) for r in controls} == set(range(3301, 3321))
            assert {int(r["key_length"]) for r in controls} == {KEY_LENGTHS[name]}
            settings.append({
                "key": name, "key_length": KEY_LENGTHS[name],
                "tested_settings": len(rows),
                "best_any": {k: best_any[k] for k in ("segment", "mode", "shift", "runes", "log_lr_nats")},
                "best_at_least_100_runes": {k: best_long[k] for k in ("segment", "mode", "shift", "runes", "log_lr_nats")},
                "positive_length": int(controls[0]["runes"]),
                "positive_passes": sum(float(r["positive_log_lr"]) >= THRESHOLD for r in controls),
                "wrong_key_passes": sum(float(r["wrong_key_log_lr"]) >= THRESHOLD for r in controls),
                "positive_score_min": min(float(r["positive_log_lr"]) for r in controls),
                "positive_score_max": max(float(r["positive_log_lr"]) for r in controls),
            })
        count = sum(float(r["log_lr_nats"]) >= THRESHOLD for r in source)
        total += len(source)
        passed += count
        stages.append({"stage": stage.upper(), "candidate_rows": len(source), "pass_rows": count,
                       "source_sha256": sha(HERE / f"source-stage_{stage}_candidates.tsv"),
                       "streams": settings})
    return {
        "schema": "liberpedia-wulfic-native-key-streams-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "source_commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
        "reading_threshold": THRESHOLD,
        "total_candidate_rows": total,
        "total_pass_rows": passed,
        "supplemental_controls_sha256": sha(HERE / "supplemental-controls.tsv"),
        "stages": stages,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    path = HERE / "results.json"
    if args.check:
        assert path.read_text(encoding="utf-8") == rendered
        print("Wulfic Stage I/M source grids and supplemental controls: OK")
    else:
        path.write_text(rendered, encoding="utf-8", newline="\n")
