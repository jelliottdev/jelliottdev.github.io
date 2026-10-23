#!/usr/bin/env python3
"""Independently check B-05 Part 2a coverage, overlap, controls and byte sensitivity."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "grid-payload-prf-seed-corner"
SOURCE = PILOT / "source/liber-primus"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    report = read(HERE / "results.json")
    rows = read(HERE / "cases.json")["cases"]
    controls = read(HERE / "control-all.json")
    equivalence = read(HERE / "key-equivalence.json")
    pilot = read(PILOT / "results.json")
    generators = [g["generator"] for g in equivalence["by_generator"]]
    expected = set(itertools.product(range(64), generators, ("mod", "reject"), (-1, 1)))
    actual = {(r["mask"], r["generator"], r["reduction"], r["sign"]) for r in rows}
    assert len(rows) == report["case_count"] == len(actual) == len(expected) == 3840
    assert actual == expected and rows == sorted(rows, key=lambda r: r["score"], reverse=True)
    assert rows[0] == report["best"] and report["hit_count"] == 0
    assert report["threshold"]["english_floor"] == -5.5
    assert report["null"]["max"] == report["threshold"]["null_max"] == pilot["null"]["max"]
    assert not [r for r in rows if r["score"] >= -5.5 and r["score"] > report["null"]["max"]]
    assert controls["case_count"] == 30 and controls["all_pass"]
    assert all(c["pass"] and all(c["gates"].values()) for c in controls["cases"])
    assert controls["one_byte_flip_sensitive_count"] == 28
    assert {c["generator"] for c in controls["cases"] if not c["one_byte_flip_sensitive"]} == {"aes128_ctr_k"}
    assert equivalence["source_invocations"] == 3840
    assert equivalence["unique_key_and_sign_cases"] == 2596
    assert equivalence["unique_across_all_generators_and_reductions"] == 2596
    unique = {g["generator"]: g["unique_per_reduction"] for g in equivalence["by_generator"]}
    assert unique["aes128_ctr_k"] == {"mod": 1, "reject": 1}
    for generator in ("aes256_ctr_k", "aes256_ctr_kiv", "chacha20_k", "chacha20_kn"):
        assert unique[generator] == {"mod": 2, "reject": 2}
    assert sum(v == {"mod": 64, "reject": 64} for v in unique.values()) == 10

    majority = (SOURCE / "analysis/pp49_51/canon_256.bin").read_bytes()
    decimal = (SOURCE / "analysis/pp49_51/canon_256_decpref.bin").read_bytes()
    differences = [i for i, pair in enumerate(zip(majority, decimal)) if pair[0] != pair[1]]
    assert len(majority) == len(decimal) == 256
    assert differences == report["contested_positions"] == [25, 175, 182, 199, 215, 237]
    assert hashlib.sha256(majority).hexdigest() == report["input_sha256"]["majority_payload"]
    assert hashlib.sha256(decimal).hexdigest() == report["input_sha256"]["decimal_preferred_payload"]

    by_config = {(r["mask"], r["generator"], r["reduction"], r["sign"]): r["score"] for r in rows}
    for old in pilot["rows"]:
        mask = 0 if old["representation"] == "maj.raw" else 63
        key = (mask, old["generator"], old["reduction"], old["sign"])
        assert by_config[key] == old["score"]
    print("3,840 source cases complete; 2,596 distinct key/sign cases; 30 planted gates; 32 pilot overlaps agree")


if __name__ == "__main__":
    main()
