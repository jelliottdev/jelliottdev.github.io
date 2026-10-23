#!/usr/bin/env python3
"""Count identical keystreams among B-05's 64 contested-byte masks."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "grid-payload-prf-seed-corner/source/liber-primus/analysis/round13/B05"))
import prf  # type: ignore[import-not-found]  # noqa: E402

OUTPUT = HERE / "key-equivalence.json"


def calculate() -> dict:
    majority, decimal = prf.load_payloads()
    by_generator = []
    signed_total = 0
    all_signed_hashes = set()
    for generator in prf.GENERATORS:
        counts = {}
        for reduction in ("mod", "reject"):
            hashes = set()
            signed_hashes = set()
            for mask in range(64):
                seed = bytearray(majority)
                for bit, position in enumerate(prf.CONTESTED):
                    if mask & (1 << bit):
                        seed[position] = decimal[position]
                key = prf.keystream(bytes(seed), generator, reduction, 1664)
                hashes.add(hashlib.sha256(bytes(key)).hexdigest())
                for sign in (-1, 1):
                    signed_hash = hashlib.sha256(bytes((sign * k) % 29 for k in key)).hexdigest()
                    signed_hashes.add(signed_hash)
                    all_signed_hashes.add(signed_hash)
            counts[reduction] = len(hashes)
            signed_total += len(signed_hashes)
        by_generator.append({"generator": generator, "unique_per_reduction": counts})
    return {"mask_count": 64, "generator_count": len(by_generator),
            "reduction_count": 2, "sign_count": 2,
            "source_invocations": 64 * len(by_generator) * 2 * 2,
            "unique_key_and_sign_cases": signed_total,
            "unique_across_all_generators_and_reductions": len(all_signed_hashes),
            "by_generator": by_generator}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding="utf-8"))
    print(f"{result['unique_key_and_sign_cases']} unique key/sign cases among "
          f"{result['source_invocations']} source invocations")


if __name__ == "__main__":
    main()
