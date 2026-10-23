"""Separate full-byte hash check on the preserved seventh-onion JPEG snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def evaluate():
    plan_raw = (HERE / "followup-plan.json").read_bytes()
    plan = json.loads(plan_raw)
    page_raw = (ROOT / plan["target_input"]["path"]).read_bytes()
    assert hashlib.sha256(page_raw).hexdigest() == plan["target_input"]["sha256"]
    literal = json.loads(page_raw)["reading"]["literal"]
    lines = [line.rstrip("/") for line in literal.splitlines() if re.fullmatch(r"[a-f0-9]+/?", line)]
    assert len(lines) == 5
    target = "".join(lines)
    assert len(target) == 128

    source_plan = json.loads((HERE / "plan.json").read_bytes())
    old_sha = {row["source_sha512"] for row in source_plan["candidates"]}
    old_b2 = {row["source_blake2b"] for row in source_plan["candidates"]}
    rows = []
    for row in plan["candidates"]:
        raw = (ROOT / row["path"]).read_bytes()
        assert len(raw) == row["bytes"]
        assert hashlib.sha256(raw).hexdigest() == row["sha256"]
        rows.append({"page": row["page"], "path": row["path"],
                     "sha512": hashlib.sha512(raw).hexdigest(),
                     "blake2b512": hashlib.blake2b(raw, digest_size=64).hexdigest()})
    assert len(rows) == 58
    planted_sha, planted_b2 = rows[0]["sha512"], rows[0]["blake2b512"]
    controls = {"sha512_archive0_recovered": [x["path"] for x in rows if x["sha512"] == planted_sha],
                "blake2b_archive0_recovered": [x["path"] for x in rows if x["blake2b512"] == planted_b2]}
    assert controls == {"sha512_archive0_recovered": [rows[0]["path"]],
                        "blake2b_archive0_recovered": [rows[0]["path"]]}
    return {
        "schema": "liberpedia-deepweb-seventh-onion-followup-v1",
        "followup_plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "source_revision": plan["source_revision"],
        "target_digest": target,
        "candidate_count": len(rows),
        "tested_digests": 2 * len(rows),
        "matches_sha512": [x["path"] for x in rows if x["sha512"] == target],
        "matches_blake2b512": [x["path"] for x in rows if x["blake2b512"] == target],
        "digest_overlap_with_primary_source_set": {
            "sha512": sum(x["sha512"] in old_sha for x in rows),
            "blake2b512": sum(x["blake2b512"] in old_b2 for x in rows)},
        "positive_controls": controls,
        "digests": rows,
        "scope_note": "Separate preserved seventh-onion byte set; not the source-exact 75 JPEG lookup."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = evaluate()
    if args.check:
        assert result == json.loads((HERE / "followup-results.json").read_bytes())
        print("PASS: 58 preserved seventh-onion JPEGs, 116 full digests and planted controls")
    else:
        (HERE / "followup-results.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"RESULT: {len(result['matches_sha512']) + len(result['matches_blake2b512'])} matches across 116 digests")
