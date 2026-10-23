"""Independent full-phase audit of Stage Y against Liberpedia's printed grid."""
from __future__ import annotations

import csv
import hashlib
import json
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
INPUTS = {"page_17.bin": "page_17.bin", "page_21.bin": "page_21.bin",
          "page_43.bin": "page_43.bin", "hint": "wisdom_hint.txt",
          "page_00-hex": "page_00-hex.bin", "onion-2-hex": "onion-2-hex.bin"}
READINGS = ("R", "R-rev", "C", "C-rev")
OPS = ("g^k", "g-k", "g+k", "k-g")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manuscript_grid() -> np.ndarray:
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 256
    assert [(int(row["sequence"]), len(row["token"])) for row in rows] == [(i, 2) for i in range(1, 257)]
    return np.array([60 * DIGITS.index(row["token"][0]) + DIGITS.index(row["token"][1])
                     for row in rows], dtype=np.uint8)


def read_grid(grid: np.ndarray, route: str) -> np.ndarray:
    if route.startswith("C"):
        grid = grid.reshape(32, 8).T.reshape(256)
    return grid[::-1] if route.endswith("rev") else grid


def operation(grid: np.ndarray, keys: np.ndarray, op: str) -> np.ndarray:
    # Cast to uint16 for transparent modulo-256 arithmetic; this is independent
    # of the source's uint8 wraparound implementation.
    g = grid.astype(np.uint16)
    k = keys.astype(np.uint16)
    if op == "g^k":
        return np.bitwise_xor(g, k).astype(np.uint8)
    if op == "g-k":
        return ((g - k) % 256).astype(np.uint8)
    if op == "g+k":
        return ((g + k) % 256).astype(np.uint8)
    if op == "k-g":
        return ((k - g) % 256).astype(np.uint8)
    raise ValueError(op)


def reverse_operation(plain: np.ndarray, key: np.ndarray, op: str) -> np.ndarray:
    p, k = plain.astype(np.uint16), key.astype(np.uint16)
    if op == "g^k":
        return np.bitwise_xor(p, k).astype(np.uint8)
    if op == "g-k":
        return ((p + k) % 256).astype(np.uint8)
    if op == "g+k":
        return ((p - k) % 256).astype(np.uint8)
    if op == "k-g":
        return ((k - p) % 256).astype(np.uint8)
    raise ValueError(op)


def windows(data: bytes) -> np.ndarray:
    source = np.frombuffer(data, dtype=np.uint8)
    at = (np.arange(len(source), dtype=np.int64)[:, None] +
          np.arange(256, dtype=np.int64)[None, :]) % len(source)
    return source[at]


def distinct(rows: np.ndarray) -> np.ndarray:
    ordered = np.sort(rows, axis=1)
    return np.count_nonzero(ordered[:, 1:] != ordered[:, :-1], axis=1) + 1


@lru_cache(maxsize=None)
def occupancy_cdf(limit: int) -> float:
    # Independent occupancy recurrence for 256 draws from 256 equiprobable
    # symbols; source uses exact Stirling numbers.
    state = np.zeros(257)
    state[0] = 1.0
    for _ in range(256):
        state = state * np.arange(257) / 256 + np.roll(state, 1) * (257 - np.arange(257)) / 256
        state[0] = 0.0
    return float(state[:limit + 1].sum())


def source_inputs(plan: dict) -> dict[str, bytes]:
    for item in plan["bundled_source_bytes"]:
        assert sha((ROOT / item["path"]).read_bytes()) == item["sha256"]
    return {name: (HERE / "inputs" / file).read_bytes() for name, file in INPUTS.items()}


def planted_controls(inputs: dict[str, bytes]) -> int:
    # 24 new deterministic unit controls: known 64-symbol text, each source
    # combined with all four byte operations at a known cyclic phase.
    message = np.arange(256, dtype=np.uint8) % 64
    count = 0
    for name, data in inputs.items():
        phase = (3301 + len(data)) % len(data)
        source = np.frombuffer(data, dtype=np.uint8)
        key = source[(phase + np.arange(256)) % len(source)]
        for op in OPS:
            cipher = reverse_operation(message, key, op)
            assert np.array_equal(operation(cipher, key, op), message), (name, op)
            assert int(distinct(message[None, :])[0]) == 64 <= 120
            count += 1
    return count


def audit() -> dict:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    grid = manuscript_grid()
    inputs = source_inputs(plan)
    with (HERE / "source-stage_y_results.tsv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    with (HERE / "source-stage_y_controls.tsv").open(encoding="utf-8", newline="") as stream:
        controls = list(csv.DictReader(stream, delimiter="\t"))
    assert sha((HERE / "source-stage_y_results.tsv").read_bytes()) == plan["source"]["source_results_sha256"]
    assert sha((HERE / "source-stage_y_controls.tsv").read_bytes()) == plan["source"]["source_controls_sha256"]
    assert len(rows) == 96 and len(controls) == 42
    assert sum(r["kind"] == "positive" and r["verdict"] == "PASS" for r in controls) == 24
    assert sum(r["kind"] == "negative" and r["verdict"] == "PASS" for r in controls) == 18
    assert all(int(r["D"]) <= 120 if r["kind"] == "positive" else int(r["D"]) > 120 for r in controls)
    assert planted_controls(inputs) == 24
    lookup = {(r["source"], r["reading"], r["op"]): r for r in rows}
    assert len(lookup) == 96
    summaries = []
    checked = 0
    for name, data in inputs.items():
        key_rows = windows(data)
        low_for_source = 257
        best_cell = None
        for route in READINGS:
            variant = read_grid(grid, route)
            for op in OPS:
                row = lookup[name, route, op]
                outputs = operation(variant[None, :], key_rows, op)
                counts = distinct(outputs)
                low = int(counts.min())
                phase = int(counts.argmin())
                assert int(row["length"]) == len(data) == int(row["trials"])
                assert int(row["min_D"]) == low and int(row["phase_at_min"]) == phase
                assert row["mean_D"] == f"{counts.mean():.2f}"
                assert row["printable_at_min"] == f"{np.isin(outputs[phase], list(range(32, 127)) + [9, 10, 13]).mean():.3f}"
                probability = occupancy_cdf(low)
                assert row["null_p_le_min"] == f"{probability:.3e}"
                assert row["expected_trials_le_min"] == f"{probability * len(data):.3g}"
                assert row["verdict"] == ("PASS" if low <= 120 else "EXCLUDED")
                if low < low_for_source:
                    low_for_source, best_cell = low, {"route": route, "op": op, "phase": phase}
                checked += len(data)
        summaries.append({"source": name, "bytes": len(data), "minimum_distinct": low_for_source,
                          "best_cell": best_cell, "cells": 16})
    assert checked == sum(len(x) for x in inputs.values()) * 16
    return {"source_revision": plan["source"]["commit"], "grid_bytes": len(grid),
            "source_count": len(inputs), "cell_count": len(rows), "phase_trials": checked,
            "source_positive_controls": 24, "source_negative_controls": 18,
            "independent_planted_controls": 24, "passing_cells": sum(r["verdict"] == "PASS" for r in rows),
            "threshold_distinct": 120, "source_summaries": summaries,
            "plan_sha256": sha((HERE / "plan.json").read_bytes())}
