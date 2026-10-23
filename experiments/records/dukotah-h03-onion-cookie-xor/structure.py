"""Retrospective, explicitly bounded structure checks on the fixed 64 outputs."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "structure-plan.json").read_text(encoding="utf-8"))
CASES = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
TARGET = bytes.fromhex("36367763ab73313a5ce0cd854ba3d6a39e4b8770")


def strict_pkcs(block: bytes) -> bool:
    if len(block) < 11 or block[:2] != b"\x00\x01":
        return False
    i = 2
    while i < len(block) and block[i] == 0xFF:
        i += 1
    return i >= 10 and i < len(block) and block[i] == 0


def independent_source_predicate(block: bytes) -> bool:
    return (len(block) >= 11 and block[:2] == b"\x00\x01" and
            any(block[2:i] == b"\xff" * (i - 2) and block[i] == 0
                for i in range(3, len(block))))


def main():
    path = HERE / "source/liber-primus/analysis/round16/zeroFP/zerofp_tests.py"
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("pinned_zerofp_structure", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    padded = b"\x00\x01" + b"\xff" * 8 + b"\x00" + b"CONTROL" + b"X" * 14
    assert len(padded) == 32 and mod.pkcs1_v15_check(padded)[0] and strict_pkcs(padded)
    assert independent_source_predicate(padded)
    digest_plant = b"start" + TARGET + b"end" + b"X" * 4
    assert len(digest_plant) == 32 and TARGET in digest_plant
    rows = []
    for case in CASES:
        block = bytes.fromhex(case["xor_hex"])
        helper, _ = mod.pkcs1_v15_check(block)
        assert helper == independent_source_predicate(block)
        rows.append({"cookie": case["cookie"], "blob": case["blob"], "offset": case["offset"],
                     "source_helper_pkcs": helper, "strict_eight_ff": strict_pkcs(block),
                     "named_digest_prefix20_substring": TARGET in block})
    result = {"schema": "liberpedia-h03-structure-diagnostic-v1", "case_count": len(rows),
              "source_helper_pkcs_hits": sum(x["source_helper_pkcs"] for x in rows),
              "strict_eight_ff_hits": sum(x["strict_eight_ff"] for x in rows),
              "named_digest_prefix20_hits": sum(x["named_digest_prefix20_substring"] for x in rows),
              "positive_controls": {"source_helper_pkcs": True, "strict_eight_ff": True,
                                    "named_digest_prefix20": True}, "cases": rows}
    (HERE / "structure-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("H-03 structure diagnostic:", result["source_helper_pkcs_hits"],
          result["strict_eight_ff_hits"], result["named_digest_prefix20_hits"])


if __name__ == "__main__":
    main()
