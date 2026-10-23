"""Check the packaged Stage R corpus, controls, result table and scorer.

Use --full to recompute all 43,500 LP2 cells from the packaged numeric data.
The default checks immutable full-table digests and selected cells spanning
all modes, key lengths and section alignments, without repeating a long run.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from fast import score

HERE = Path(__file__).resolve().parent
MODES = {"sub": 0, "add": 1, "beaufort": 2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_profile():
    with np.load(HERE / "source-profile.npz", allow_pickle=False) as data:
        labels = json.loads(data["labels"].tobytes().decode("utf-8"))
        keys = {name: np.asarray(data[f"key_{i}"], dtype=np.int64)
                for i, name in enumerate(labels["names"])}
        ciphers = {name: np.asarray(data[f"segment_{i}"], dtype=np.int64)
                   for i, name in enumerate(labels["segments"])}
        ratio = np.asarray(data["ratio"], dtype=np.float64)
        plain = np.asarray(data["plain"], dtype=np.int64)
    if len(keys) != 50 or len(ciphers) != 10 or len(ratio) != 29 or not len(plain):
        raise AssertionError("Bad numeric profile dimensions")
    if any(np.any((item < 0) | (item >= 29)) for item in [*keys.values(), *ciphers.values(), plain]):
        raise AssertionError("A rune number is outside GP29")
    if np.any(ratio <= 0):
        raise AssertionError("Emission ratio must be positive")
    if labels["by_cost"] != sorted(keys, key=lambda name: -len(keys[name])):
        raise AssertionError("Unexpected source key order")
    return keys, ciphers, ratio


def table(path: Path, expected_hash: str, expected_count: int):
    if sha(path) != expected_hash:
        raise AssertionError(f"Archived source table changed: {path.name}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != expected_count:
        raise AssertionError(f"Wrong row count in {path.name}")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Recompute all 43,500 LP2 cells")
    args = parser.parse_args()
    keys, ciphers, ratio = load_profile()
    controls = table(HERE / "source-stage_r_controls.tsv",
                     "e302f6009e63ba17de950ad396be2001a2c922d047e0da83b22990efefb6a29b", 200)
    candidates = table(HERE / "source-stage_r_candidates.tsv",
                       "7636b6e93acc24f221ce5e7ef70419a17ff238c3a0d94becb69ece22707d1949", 43500)
    if min(float(row["positive_log_lr"]) for row in controls) < 30:
        raise AssertionError("Source positive-control gate failed")
    if max(float(row["negative_log_lr"]) for row in controls) >= 30:
        raise AssertionError("Source negative-control gate failed")
    if sum(float(row["log_lr_nats"]) >= 30 for row in candidates):
        raise AssertionError("Source candidate pass count changed")
    if max(float(row["log_lr_nats"]) for row in candidates) != 2.41:
        raise AssertionError("Source candidate maximum changed")
    selected = range(len(candidates)) if args.full else [
        0,1,28,29,86,87, 200, 260, 520, 870, 2600, 2900,
        7000, 9000, 12000, 18000, 23000, 32000, 40000, 43499
    ]
    for i in selected:
        row = candidates[i]
        key, cipher = keys[row["key"]], ciphers[row["segment"]]
        if len(cipher) != int(row["runes"]):
            raise AssertionError((i, "segment length"))
        value = score(cipher, key, ratio, MODES[row["mode"]], int(row["shift"]))
        if f"{value:.2f}" != row["log_lr_nats"]:
            raise AssertionError((i, "numeric score", value, row["log_lr_nats"]))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    if result["candidate_count"] != len(candidates) or result["control_count"] != len(controls):
        raise AssertionError("Result summary counts changed")
    if result["candidate_pass_count"] != 0 or result["candidate_max_rounded"] != 2.41:
        raise AssertionError("Result summary finding changed")
    if result["title_runes"] != len(ciphers["10"]) or result["title_settings"] != sum(row["segment"] == "10" for row in candidates):
        raise AssertionError("Short-title count changed")
    upper = len(ciphers["10"]) * math.log(float(max(ratio)))
    if abs(result["title_absolute_score_bound"] - upper) > 1e-12 or upper >= 30:
        raise AssertionError("Short-title impossibility bound changed")
    if result["best_non_title_rounded"] != max(float(row["log_lr_nats"]) for row in candidates if row["segment"] != "10"):
        raise AssertionError("Non-title maximum changed")
    if result["joined_max_rounded"] != max(float(row["log_lr_nats"]) for row in candidates if row["segment"] == "7-15"):
        raise AssertionError("Joined-stream maximum changed")
    print(f"PASS: {len(selected)} computed scores, {len(candidates)} source-table rows, {len(controls)} controls")


if __name__ == "__main__":
    main()
