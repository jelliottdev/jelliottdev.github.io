"""Independent grid, source-key and manuscript checks for Stages I/M."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SIBLING = ROOT / "experiments/records/wulfic-stage-ab-reset-alphabets"
BASE60 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
MODES = ("sub", "add", "beaufort")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t" if path.suffix == ".tsv" else ","))


def fingerprint(values: list[int]) -> str:
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def grid_streams() -> dict[str, list[int]]:
    entries = rows(ROOT / "exports/alphanumeric-grids.csv")
    assert len(entries) == 256 and {int(e["sequence"]) for e in entries} == set(range(1, 257))
    tokens = [e["token"] for e in sorted(entries, key=lambda e: int(e["sequence"]))]
    assert all(len(token) == 2 and all(ch in BASE60 for ch in token) for token in tokens)
    numbers = [60 * BASE60.index(token[0]) + BASE60.index(token[1]) for token in tokens]
    assert max(numbers) <= 255
    bits = "".join(f"{number:08b}" for number in numbers)
    return {
        "G-B bytes": [number % 29 for number in numbers],
        "G-5 5-bit groups": [int(bits[i:i + 5], 2) % 29 for i in range(0, len(bits) - 4, 5)],
        "G-D base-60 digits": [BASE60.index(ch) % 29 for token in tokens for ch in token],
    }


def primes(count: int) -> list[int]:
    out = []
    candidate = 2
    while len(out) < count:
        prime = True
        limit = isqrt(candidate)
        for p in out:
            if p > limit:
                break
            if candidate % p == 0:
                prime = False
                break
        if prime:
            out.append(candidate)
        candidate += 1
    return out


def check() -> None:
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["plan_sha256"] == hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest()
    for item in plan["inputs"]:
        assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
    expected = plan["source_key_fingerprints"]
    assert fingerprint(primes(25912)) == expected["K-A primes"]
    for name, values in grid_streams().items():
        assert fingerprint(values) == expected[name]
        assert len(values) == next(s["key_length"] for stage in result["stages"]
                                     for s in stage["streams"] if s["key"] == name)
    # Compare the independent site transcription with the pinned source layout.
    spec = importlib.util.spec_from_file_location("site_reader", SIBLING / "check.py")
    assert spec and spec.loader
    site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(site)
    runes, unit_ids = site.manuscript()
    layout = json.loads((SIBLING / "layout.json").read_text(encoding="utf-8"))
    assert runes == layout["runes"] and len(runes) == 12956
    lengths = site.summarize(unit_ids["segment"])[0]
    assert lengths == layout["unit_lengths"]["segment"]
    expected_length = {str(i + 7): length for i, length in enumerate(lengths)}
    controls = rows(HERE / "supplemental-controls.tsv")
    assert len(controls) == 120
    for stage in result["stages"]:
        tag = stage["stage"].lower()
        grid = rows(HERE / f"source-stage_{tag}_candidates.tsv")
        keys = {s["key"] for s in stage["streams"]}
        assert {row["key"] for row in grid} == keys
        places = ([str(i) for i in range(7, 16)] + ["7-15"] if tag == "i" else
                  [f"section {i}" for i in range(7, 16)] +
                  ["LP2 continuous", "after the grid", "ending at the grid"])
        expected_cells = {(key, place, mode, shift) for key in keys for place in places
                          for mode in MODES for shift in range(29)}
        actual_cells = {(r["key"], r["segment"], r["mode"], int(r["shift"])) for r in grid}
        assert len(grid) == len(actual_cells) == len(expected_cells) and actual_cells == expected_cells
        assert len(grid) == stage["candidate_rows"]
        assert sum(float(r["log_lr_nats"]) >= 30 for r in grid) == stage["pass_rows"] == 0
        for r in grid:
            place = r["segment"]
            if place in ("7-15", "LP2 continuous"):
                assert int(r["runes"]) == len(runes)
            elif place.startswith("section "):
                assert int(r["runes"]) == expected_length[place.split()[1]]
            elif place in expected_length:
                assert int(r["runes"]) == expected_length[place]
            elif place == "after the grid":
                assert int(r["runes"]) == 842
            elif place == "ending at the grid":
                target = next(s["key_length"] for s in stage["streams"] if s["key"] == r["key"])
                assert int(r["runes"]) == target
            else:
                raise AssertionError(place)
        for stream in stage["streams"]:
            subset = [r for r in controls if r["source"] == stream["key"]]
            assert len(subset) == 20 and {int(r["seed"]) for r in subset} == set(range(3301, 3321))
            assert {int(r["runes"]) for r in subset} == {stream["positive_length"]}
            assert sum(float(r["positive_log_lr"]) >= 30 for r in subset) == stream["positive_passes"]
            assert sum(float(r["wrong_key_log_lr"]) >= 30 for r in subset) == stream["wrong_key_passes"]
    assert result["total_candidate_rows"] == 5742 and result["total_pass_rows"] == 0
    print("Independent grid, source-key, manuscript and supplemental-control checks: OK")


if __name__ == "__main__":
    check()
