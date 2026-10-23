#!/usr/bin/env python3
"""Independent coverage and overlap checks for the B-05 source-grid replay."""
from __future__ import annotations

import itertools
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "grid-payload-prf-seed-corner"
MASKS = HERE.parent / "grid-payload-prf-contested-masks"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    report = read(HERE / "results.json")
    rows = [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    source2a = read(MASKS / "cases.json")["cases"]
    pilot = read(PILOT / "results.json")["rows"]
    source_manifest = read(PILOT / "source-manifest.json")
    for item in source_manifest["files"]:
        path = PILOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    assert len(rows) == report["case_count"] == 66840
    assert report["prior_part2a_cases_reused"] == len(source2a) == 3840
    assert report["seeded_unique_scores"] == 2596
    assert report["unique_effective_keys_all_parts"] == 59948
    assert report["new_unique_scores"] == 59948 - 2596
    assert report["english_score_floor"] == -5.5
    assert report["source_null_max"] == -7.001322

    names = [r["generator"] for r in read(MASKS / "key-equivalence.json")["by_generator"]]
    reps = [p + "." + suffix for p in ("maj", "dec")
            for suffix in ("raw", "byterev", "bitrev8", "bitrevall", "swap32", "hexascii")]
    offsets = (0, 1, 2, 3, 5, 8, 13, 29, 64, 128, 256, 512, 1024, 3301)
    grids = {"part1": set(), "shift": set(), "part2b": set()}
    by_hash = {}
    for row in rows:
        assert row["part"] in grids and math.isfinite(row["score"])
        digest = row["effective_key_sha256"]
        assert len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)
        if digest in by_hash:
            assert by_hash[digest] == row["score"]
        by_hash[digest] = row["score"]
        if row["part"] == "part1":
            key = (row["rep"], row["gen"], row["red"], row["sign"],
                   row["direction"], row["atbash"], row["offset"])
        elif row["part"] == "shift":
            key = (row["rep"], row["gen"], row["red"], row["shift"], row["sign"])
        else:
            key = (row["index"], row["value"], row["gen"])
        assert key not in grids[row["part"]]
        grids[row["part"]].add(key)
    assert grids["part1"] == set(itertools.product(
        reps, names, ("mod", "reject"), (-1, 1), ("fwd", "rev"), (False, True), offsets))
    assert grids["shift"] == set(itertools.product(
        ("maj.raw", "dec.raw"), names, ("mod", "reject"), range(29), (-1, 1)))
    assert grids["part2b"] == set(itertools.product(
        (25, 175, 182, 199, 215, 237), range(256), names))

    score_by_main = {(r["rep"], r["gen"], r["red"], r["sign"]): r["score"] for r in rows
                     if r["part"] == "part1" and r["direction"] == "fwd"
                     and not r["atbash"] and r["offset"] == 0
                     and r["rep"] in ("maj.raw", "dec.raw")}
    score_by_shift = {(r["rep"], r["gen"], r["red"], r["sign"]): r["score"] for r in rows
                      if r["part"] == "shift" and r["shift"] == 0}
    assert score_by_main == score_by_shift
    mask_corners = {("maj.raw" if r["mask"] == 0 else "dec.raw", r["generator"],
                     r["reduction"], r["sign"]): r["score"] for r in source2a
                    if r["mask"] in (0, 63)}
    assert score_by_main == mask_corners
    for old in pilot:
        key = (old["representation"], old["generator"], old["reduction"], old["sign"])
        assert score_by_main[key] == old["score"]

    score_by_single = {(r["index"], r["value"], r["gen"]): r["score"] for r in rows
                       if r["part"] == "part2b"}
    majority = (PILOT / "source/liber-primus/analysis/pp49_51/canon_256.bin").read_bytes()
    decimal = (PILOT / "source/liber-primus/analysis/pp49_51/canon_256_decpref.bin").read_bytes()
    source2a_lookup = {(r["mask"], r["generator"], r["reduction"], r["sign"]): r["score"]
                       for r in source2a}
    for bit, index in enumerate((25, 175, 182, 199, 215, 237)):
        for name in names:
            assert score_by_single[(index, majority[index], name)] == score_by_main[
                ("maj.raw", name, "mod", -1)]
            assert score_by_single[(index, decimal[index], name)] == source2a_lookup[
                (1 << bit, name, "mod", -1)]
    for part in grids:
        subset = [r for r in rows if r["part"] == part]
        expected_best = max(subset, key=lambda r: r["score"])
        assert report["by_part"][part]["cases"] == len(subset)
        assert report["by_part"][part]["best"] == expected_best
        assert report["by_part"][part]["hits"] == sum(r["score"] >= -5.5 for r in subset)
    print("66,840 source cases complete; all grid cells, duplicate scores and 32+120+90 overlaps agree")


if __name__ == "__main__":
    main()
