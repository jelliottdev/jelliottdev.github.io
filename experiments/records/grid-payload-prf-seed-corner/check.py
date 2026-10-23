#!/usr/bin/env python3
"""Fast independent checks of the saved B-05 corner and PRF primitives."""
from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/liber-primus"
sys.path.insert(0, str(SOURCE / "analysis/round13/B05"))
import prf  # type: ignore[import-not-found]  # noqa: E402


def rc4_reference(key: bytes, length: int) -> bytes:
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) % 256
        state[i], state[j] = state[j], state[i]
    i = j = 0
    out = bytearray()
    for _ in range(length):
        i = (i + 1) % 256
        j = (j + state[i]) % 256
        state[i], state[j] = state[j], state[i]
        out.append(state[(state[i] + state[j]) % 256])
    return bytes(out)


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    rows = result["rows"]
    expected = set(itertools.product(
        ("maj.raw", "dec.raw"),
        ("sha256_ctr", "rc4", "hmac_drbg_sha256", "aes256_ctr_k"),
        ("mod", "reject"),
        (-1, 1),
    ))
    actual = {(r["representation"], r["generator"], r["reduction"], r["sign"]) for r in rows}
    assert len(rows) == result["case_count"] == len(actual) == len(expected) == 32
    assert actual == expected
    best = max(rows, key=lambda row: row["score"])
    assert result["best"] == best
    assert best["score"] == -7.104663
    assert best["score"] < result["null"]["max"] == -7.001322
    assert not result["hits"]
    assert not [r for r in rows if r["score"] >= result["threshold"]["english_floor"]
                                and r["score"] > result["threshold"]["null_max"]]
    assert len(result["control"]["cases"]) == 4 and result["control"]["all_pass"]
    for case in result["control"]["cases"]:
        assert case["correct_score"] == -4.17
        assert case["correct_score"] > result["threshold"]["english_floor"]
        assert case["correct_score"] > case["wrong_score"] + 1
        assert case["correct_score"] > case["one_byte_flip_score"] + 1
    payloads = (
        SOURCE / "analysis/pp49_51/canon_256.bin",
        SOURCE / "analysis/pp49_51/canon_256_decpref.bin",
    )
    for label, path in zip(("majority_payload", "decimal_preferred_payload"), payloads):
        seed = path.read_bytes()
        assert len(seed) == 256
        assert hashlib.sha256(seed).hexdigest() == result["input_sha256"][label]
        # Check the source counter definition against hashlib, without using its helper.
        first_block = hashlib.sha256(seed + (0).to_bytes(4, "big")).digest()
        assert prf.GENERATORS["sha256_ctr"](seed, 32) == first_block
        # Independently implement RC4's state update for this exact seed.
        assert prf.GENERATORS["rc4"](seed, 64) == rc4_reference(seed, 64)
    assert rc4_reference(b"Key", 10).hex() == "eb9f7781b734ca72a719"
    assert all(x == b % 29 for x, b in zip(prf.keystream(payloads[0].read_bytes(), "sha256_ctr", "mod", 32),
                                            prf.GENERATORS["sha256_ctr"](payloads[0].read_bytes(), 32)))
    print("32-case Cartesian grid, score gate, planted controls, payloads and PRF spot checks pass")


if __name__ == "__main__":
    main()
