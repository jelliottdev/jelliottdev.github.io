"""Independently reconstruct every H-03 XOR case without source imports."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "replay-plan.json").read_text(encoding="utf-8"))
SRC = HERE / "source/liber-primus/analysis"


def main():
    cookies = []
    for name in PLAN["case_grid"]["cookies"]:
        raw = (SRC / "armada20" / name).read_text(encoding="utf-8")
        value = bytes.fromhex("".join(raw.split()))
        assert len(value) == 32
        cookies.append((name.replace("key_", "").replace(".txt", ""), value))
    files = {
        "canon_256.bin": SRC / "pp49_51/canon_256.bin",
        "rsahex_cu343_761.bin": SRC / "armada_osint/onions_ibotpeaches/rsahex_cu343_761.bin",
        "rsahex_fv7ly_1033.bin": SRC / "armada_osint/onions_ibotpeaches/rsahex_fv7ly_1033.bin",
        "rsahex_avowy_3301.bin": SRC / "armada_osint/onions_ibotpeaches/rsahex_avowy_3301.bin",
    }
    blobs = [(name.replace(".bin", "").replace("_761", "").replace("_1033", "").replace("_3301", ""), files[name].read_bytes())
             for name in PLAN["case_grid"]["blobs"]]
    assert all(len(blob) == 256 for _, blob in blobs)
    cases = []
    for cookie_name, cookie in cookies:
        for blob_name, blob in blobs:
            for start in PLAN["case_grid"]["offsets"]:
                block = blob[start:start + 32]
                out = bytes(a ^ b for a, b in zip(cookie, block))
                printable = sum(32 <= byte <= 126 for byte in out)
                cases.append({"cookie": cookie_name, "blob": blob_name, "offset": start,
                              "printable_count": printable, "printable_ratio": printable / 32,
                              "xor_hex": out.hex(), "two_byte_null_hint": out[:2] == b"\x00\x01"})
    assert len(cases) == 64
    got = json.loads((HERE / "results.json").read_text(encoding="utf-8"))["source"]
    expected = json.loads((SRC / "round16/zeroFP/results.json").read_text(encoding="utf-8"))["H-03"]
    assert got == expected, "source replay differs from its saved summary"
    assert got["trials"] == len(cases)
    assert got["max_printable"] == max(row["printable_ratio"] for row in cases)
    assert not got["hits"] and not any(row["printable_count"] >= 26 for row in cases)
    assert got["max_printable"] == 20 / 32
    assert not any(row["two_byte_null_hint"] for row in cases)
    output = {"schema": "liberpedia-h03-independent-cases-v1", "case_count": 64,
              "max_printable_count": 20, "max_printable_ratio": 0.625,
              "printable_gate_hits": 0, "two_byte_null_hints": 0, "cases": cases}
    (HERE / "cases.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("H-03 independent 64-case XOR recount matches source; 0/64 printable hits; max 20/32")


if __name__ == "__main__":
    main()
