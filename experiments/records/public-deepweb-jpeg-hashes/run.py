"""Replay the pinned 75-JPEG full-file hash lookup."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def evaluate() -> dict:
    plan_raw = (HERE / "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    page_raw = (ROOT / plan["target_input"]["path"]).read_bytes()
    assert hashlib.sha256(page_raw).hexdigest() == plan["target_input"]["sha256"]
    literal = json.loads(page_raw)["reading"]["literal"]
    pieces = [line.rstrip("/") for line in literal.splitlines() if re.fullmatch(r"[0-9a-f]+/?", line)]
    assert len(pieces) == 5
    target = "".join(pieces)
    assert len(target) == 128

    matches = {"sha512": [], "blake2b512": []}
    digest_pairs = []
    for candidate in plan["candidates"]:
        raw = (ROOT / candidate["path"]).read_bytes()
        assert len(raw) == candidate["bytes"]
        assert hashlib.sha256(raw).hexdigest() == candidate["sha256"]
        sha = hashlib.sha512(raw).hexdigest()
        b2 = hashlib.blake2b(raw, digest_size=64).hexdigest()
        assert sha == candidate["source_sha512"] and b2 == candidate["source_blake2b"]
        digest_pairs.append((candidate["source_number"], sha, b2))
        if sha == target:
            matches["sha512"].append(candidate["path"])
        if b2 == target:
            matches["blake2b512"].append(candidate["path"])
    assert len(digest_pairs) == 75
    first = plan["candidates"][0]
    controls = {
        "sha512_image00_recovered": [c["path"] for c in plan["candidates"] if c["source_sha512"] == first["source_sha512"]],
        "blake2b_image00_recovered": [c["path"] for c in plan["candidates"] if c["source_blake2b"] == first["source_blake2b"]],
    }
    assert controls == {"sha512_image00_recovered": [first["path"]],
                        "blake2b_image00_recovered": [first["path"]]}
    return {
        "schema": "liberpedia-public-deepweb-jpeg-hashes-results-v1",
        "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "source_revision": plan["source_revision"],
        "target_page": "lp2-56",
        "target_digest": target,
        "candidate_count": len(digest_pairs),
        "source_table_full_sha512_matches": len(digest_pairs),
        "source_table_full_blake2b_matches": len(digest_pairs),
        "tested_digests": len(digest_pairs) * 2,
        "target_matches": matches,
        "positive_controls": controls,
        "scope_note": "Full exact JPEG bytes matching the pinned source checksum table. This is not a search of arbitrary deep-web pages."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = evaluate()
    if args.check:
        assert report == json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        print("PASS: 75 exact source JPEGs, 150 digests, target lookup and planted controls")
    else:
        (HERE / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"RESULT: {sum(map(len, report['target_matches'].values()))} matches across 150 digests")
