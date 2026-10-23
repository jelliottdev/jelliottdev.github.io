#!/usr/bin/env python3
"""Freeze two available 512-bit hash algorithms before testing old input corpus."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OLD = ROOT / "experiments/records/lp2-56-internal-artifact-hashes/plan.json"
DLL = Path(r"C:\Program Files\GnuPG\bin\libgcrypt-20.dll")


def main():
    if (HERE / "plan.json").exists():
        raise SystemExit("Frozen plan already exists")
    source_bytes = OLD.read_bytes()
    source = json.loads(source_bytes)
    assert len(source["target"]["hex"]) == 128 and len(source["pages"]) == 75 and len(source["sections"]) == 9
    assert DLL.exists()
    dll_bytes = DLL.read_bytes()
    plan = {
        "schema": "liberpedia-lp2-56-whirlpool-stribog-plan-v1",
        "question": "Do the two additional installed 512-bit digests of the previously frozen Liberpedia artifact bytes equal LP2-56's complete printed value?",
        "source_plan": {"path": OLD.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(source_bytes).hexdigest()},
        "target": source["target"],
        "library": {"name": "libgcrypt", "version": "1.12.2", "local_path": str(DLL),
                    "sha256": hashlib.sha256(dll_bytes).hexdigest(), "bytes": len(dll_bytes),
                    "api": "gcry_md_map_name, gcry_md_get_algo_dlen, gcry_md_hash_buffer"},
        "algorithms": [
            {"id": "whirlpool", "libgcrypt_name": "WHIRLPOOL", "digest_display": ["byte-order"]},
            {"id": "stribog512", "libgcrypt_name": "STRIBOG512", "digest_display": ["byte-order", "rfc6986-display"]}
        ],
        "controls": [
            {"algorithm": "whirlpool", "id": "abc", "input_hex": "616263", "expected_hex": "4e2448a4c6f486bb16b6562c73b4020bf3043e3a731bce721ae1b303d97e6d4c7181eebdb6c57e277d0e34957114cbd6c797fc9d95d8b582d225292076d4eef5", "rule": "Input and output in ordinary byte order; Whirlpool reference vector."},
            {"algorithm": "stribog512", "id": "rfc6986-m1", "input_hex": "323130393837363534333231303938373635343332313039383736353433323130393837363534333231303938373635343332313039383736353433323130", "expected_hex": "486f64c1917879417fef082b3381a4e211c324f074654c38823a7b76f830ad00fa1fbae42b1285c0352f227524bc9ab16254288dd6863dccd5b9f54a1ad0541b", "rule": "RFC 6986 displays vectors most-significant byte first; reverse displayed input bytes for a normal byte API, and reverse output bytes to compare with this displayed digest."},
            {"algorithm": "stribog512", "id": "rfc6986-m2", "input_hex": "fbe2e5f0eee3c820fbeafaebef20fffbf0e1e0f0f520e0ed20e8ece0ebe5f0f2f120fff0eeec20f120faf2fee5e2202ce8f6f3ede220e8e6eee1e8f0f2d1202ce8f0f2e5e220e5d1", "expected_hex": "28fbc9bada033b1460642bdcddb90c3fb3e56c497ccd0f62b8a2ad4935e85f037613966de4ee00531ae60f3b5a47f8dae06915d5f2f194996fcabf2622e6881e", "rule": "Same RFC 6986 byte-order conversion as M1."}
        ],
        "candidate_policy": "Reuse exactly the 412 named byte variants in the pinned source plan, including duplicates; hash the 324 distinct byte strings once per algorithm then fan out. No new input transformation.",
        "comparison_policy": "Whirlpool digest bytes in hex, Stribog digest bytes in hex and their byte-reversed RFC 6986 display form; compare all 128 hex digits with the printed target. The second Stribog display is a representation, not a distinct hash function.",
        "noncoverage": "No arbitrary inputs, salted hashes, partial matching, bit/nibble reversal, Whirlpool-0/T revisions, or other library-specific transforms.",
        "declared_before_run": "2026-10-23"
    }
    (HERE / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("Frozen source corpus, libgcrypt version and three independent algorithm controls")


if __name__ == "__main__":
    main()
