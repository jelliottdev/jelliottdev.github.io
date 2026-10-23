"""Pre-manuscript positive and exact-source-function parity checks."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import runpy
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from engine import scan_masks, source_weights
from snapshot_inputs import COMMIT, HERE, git_bytes


def load_source(source_root: Path) -> dict:
    source = git_bytes(source_root, "tools/legacy/p21_30_second_layer.py")
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "p21_30_second_layer.py"
        path.write_bytes(source)
        return runpy.run_path(str(path), run_name="source_functions_only")


def scalar(cipher: list[int], key: list[int], mode: str, mask: set[int]) -> list[int]:
    out = []
    ki = 0
    for i, c in enumerate(cipher):
        if i in mask:
            assert c == 0
            out.append(0)
            continue
        k = key[ki % len(key)]
        out.append(((c-k) if mode == "sub" else (c+k) if mode == "add" else (k-c)) % 29)
        ki += 1
    return out


def scalar_ioc(values: list[int]) -> float:
    f = collections.Counter(values)
    return 29 * sum(v * (v - 1) for v in f.values()) / (len(values) * (len(values) - 1))


def build(source_root: Path) -> dict:
    pin = json.loads((HERE / "inputs.json").read_text(encoding="utf8"))
    assert pin["script_blob"] == "1e93873d5794bb1149826adc79c14cc76c4c830d"
    assert len(pin["pages"]) == 10 and max(p["F_count"] for p in pin["pages"]) == 14
    source = load_source(source_root)
    key = source["parse_keyword"]("CABAL")
    assert key == [5, 24, 17, 24, 20]
    literal_positions = {4, 11}
    planted, cipher = [], []
    ki = 0
    for i in range(20):
        if i in literal_positions:
            planted.append(0)
            cipher.append(0)
            continue
        k = key[ki % len(key)]
        p = 10 if i == 0 else 24 if i == 5 else (k - 1) % 29
        c = (k - p) % 29  # source Beaufort
        assert c != 0
        planted.append(p)
        cipher.append(c)
        ki += 1
    assert {i for i, c in enumerate(cipher) if c == 0} == literal_positions
    words = [planted[:1], planted[1:5], planted[5:6], planted[6:]]
    assert source["check_singletons"](planted, words)[:2] == (2, 2)
    assert source["decrypt_with_fskip"](cipher, key, "beaufort", literal_positions) == planted
    assert scalar(cipher, key, "beaufort", literal_positions) == planted
    assert source["ioc"](planted) == scalar_ioc(planted)
    assert source["score_text"](planted) > 0
    small = [7, 0, 4, 0, 19, 0, 2, 8, 0]
    zeroes = [i for i, c in enumerate(small) if c == 0]
    parity = 0
    for mode in ("sub", "add", "beaufort"):
        for bits in range(1 << len(zeroes)):
            mask = {zeroes[j] for j in range(len(zeroes)) if bits >> j & 1}
            assert source["decrypt_with_fskip"](small, key, mode, mask) == scalar(small, key, mode, mask)
            parity += 1
    weights = source_weights(git_bytes(source_root, "tools/legacy/p21_30_second_layer.py"))
    singleton = np.zeros(len(planted), dtype=np.uint8)
    singleton[0] = singleton[5] = 1
    fast = scan_masks(np.array(cipher, dtype=np.int16), np.array(key, dtype=np.int16),
                      2, singleton, weights)
    expected_valid = []
    for bits in range(4):
        mask = {p for j, p in enumerate(sorted(literal_positions)) if bits >> j & 1}
        dec = source["decrypt_with_fskip"](cipher, key, "beaufort", mask)
        if source["check_singletons"](dec, [dec[:1], dec[1:5], dec[5:6], dec[6:]])[:2] == (2, 2):
            expected_valid.append((source["ioc"](dec) * 100 + source["score_text"](dec) * .5, bits))
    assert fast[0] == 2 and fast[1] == 2 and fast[2] == len(expected_valid)
    assert abs(fast[5] - max(v[0] for v in expected_valid)) < 1e-9
    assert fast[6] == max(expected_valid, key=lambda x: x[0])[1]
    return {"schema": "wulfic-p21-gate-v1", "source_commit": COMMIT,
            "source_blob": pin["script_blob"], "input_snapshot_sha256": hashlib.sha256((HERE / "inputs.json").read_bytes()).hexdigest(),
            "planted_20_rune_literal_positions": sorted(literal_positions),
            "planted_full_recovery": True, "planted_singletons_passing": 2,
            "independent_source_recurrence_comparisons": parity,
            "compiled_full_mask_plant_parity": True,
            "source_ioc_and_bigram_score_positive": True,
            "max_source_F_count": 14}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(build(args.source_root), indent=2).encode("utf8") + b"\n"
    out = HERE / "gate.json"
    if args.check:
        assert out.read_bytes() == raw
    else:
        out.write_bytes(raw)
    print("Pre-outcome planted literal-F and 48 scalar/source comparisons passed.")


if __name__ == "__main__":
    main()
