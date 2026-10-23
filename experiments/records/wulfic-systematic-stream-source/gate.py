"""Pre-outcome source parity and planted-detection controls."""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import subprocess
from pathlib import Path

import numpy as np

from engine import GOOD_MASK, MODES, decode, lfsr_grid, lfsr_key, score, singleton_positions, stream, stream_names, tuple_from_index

HERE = Path(__file__).resolve().parent
SOURCE_BLOB = "0a588175f9a1b7537740803876d762ab542b50a7"


def source_module(root: Path):
    root = root.resolve()
    path = root / "tools" / "legacy" / "stream_cipher_attack.py"
    assert subprocess.check_output(["git", "-C", str(root), "hash-object", str(path)]).decode().strip() == SOURCE_BLOB
    spec = importlib.util.spec_from_file_location("pinned_stream_source", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_stream(module, name: str, length: int):
    if name.startswith("totient_s"):
        return module.totient_stream(int(name.split("s")[-1]), length)
    if name.startswith("prime_mod_s"):
        return module.prime_mod_stream(int(name.split("s")[-1]), length)
    if name.startswith("cumul_totient_s"):
        return module.cumulative_totient_stream(int(name.split("s")[-1]), length)
    if name.startswith("prime_gap_s"):
        return module.prime_gap_stream(int(name.split("s")[-1]), length)
    sub = int(name[len("prime_minus"):-len("_s0")])
    return module.prime_minus_stream(0, length, sub)


def words_from_lengths(values: list[int], lengths: list[int]) -> list[list[int]]:
    words = []; pos = 0
    for length in lengths:
        words.append(values[pos:pos+length]); pos += length
    assert pos == len(values)
    return words


def run_gate(root: Path) -> dict:
    module = source_module(root)
    rng = random.Random(20261023)
    for name in stream_names():
        for length in (1, 7, 45, 279):
            assert stream(name, length).tolist() == source_stream(module, name, length)
    sampled = [0, 1, 28, 29, 29 ** 2, 29 ** 3, 29 ** 4 - 1]
    sampled += [rng.randrange(29 ** 4) for _ in range(100)]
    random_values = [rng.randrange(29) for _ in range(41)]
    lengths = [1, 3, 1, 4, 1, 5, 1, 4, 1, 5, 1, 5, 1, 5, 3]
    assert sum(lengths) == len(random_values)
    singles = singleton_positions(lengths)
    flags = np.zeros(len(random_values), dtype=np.uint8); flags[singles] = 1
    values = np.asarray(random_values, dtype=np.int16)
    scores, hits = lfsr_grid(values, flags, GOOD_MASK)
    words = words_from_lengths(random_values, lengths)
    for idx in sampled:
        params = tuple_from_index(idx)
        assert lfsr_key(params, len(values)).tolist() == module.lfsr_keystream(params[:2], params[2:], len(values))
        key = lfsr_key(params, len(values))
        for mi, mode in enumerate(MODES):
            sioc, sbg, ssh, st, splain = module.score_decrypt(random_values, words, key.tolist(), mode)
            own = score(values, key, singles, mode)
            assert own["ioc"] == sioc and own["bigrams"] == sbg
            assert own["single_hits"] == ssh and own["single_total"] == st
            assert decode(values, key, mode).tolist() == splain
            assert abs(scores[idx, mi] - own["combined"]) < 1e-12
            assert bool(hits[idx, mi]) == (own["combined"] > 3.0)
    # Detection controls use declared source singleton locations and a full planted page.
    plaintext = np.asarray([(i * 7 + 4) % 29 for i in range(len(values))], dtype=np.int16)
    plaintext[singles] = np.asarray([10 if i % 2 == 0 else 24 for i in range(len(singles))], dtype=np.int16)
    skey = stream("prime_gap_s1", len(values))
    lkey = lfsr_key((4, 0, 0, 13), len(values))  # includes a zero state and zero tap
    for key, kind in ((skey, "prime_gap_s1"), (lkey, "LFSR(4,0,0,13)")):
        for mode in MODES:
            if mode == "sub":
                cipher = (plaintext + key) % 29
            elif mode == "add":
                cipher = (plaintext - key) % 29
            else:
                cipher = (key - plaintext) % 29
            recovered = decode(cipher, key, mode)
            assert np.array_equal(recovered, plaintext)
            result = score(cipher, key, singles, mode)
            assert result["single_hits"] == result["single_total"]
            assert result["combined"] > (3.0 if kind.startswith("LFSR") else 2.0)
    return {"schema": "wulfic-stream-gate-v1", "source_blob": SOURCE_BLOB,
            "all_26_generators_parity_lengths": [1, 7, 45, 279],
            "lfsr_tuple_samples": len(sampled), "lfsr_modes": list(MODES),
            "lfsr_includes_zero_state_tap_cases": True,
            "source_score_parity": True, "planted_full_plaintext_recovery": True,
            "planted_source_screen": True}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run_gate(args.source_root)
    target = HERE / "gate.json"
    raw = json.dumps(result, indent=2).encode("utf8") + b"\n"
    if args.check:
        assert target.read_bytes() == raw
    else:
        target.write_bytes(raw)
    print("Source parity and planted gates passed.")


if __name__ == "__main__":
    main()
