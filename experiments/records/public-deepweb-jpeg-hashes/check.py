"""Independently hash the frozen source-matched JPEGs and read the printed target."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

plan_bytes = (HERE / "plan.json").read_bytes()
plan = json.loads(plan_bytes)
saved = json.loads((HERE / "results.json").read_bytes())
assert hashlib.sha256(plan_bytes).hexdigest() == saved["plan_sha256"]
page_bytes = (ROOT / "data/pages/lp2-56.json").read_bytes()
assert hashlib.sha256(page_bytes).hexdigest() == plan["target_input"]["sha256"]
page = json.loads(page_bytes)
assert page["id"] == "lp2-56"
printed = [line["raw"].strip("/") for line in page["lines"]
           if re.fullmatch(r"[a-f0-9]{20,32}/?", line["raw"])]
assert len(printed) == 5
target = "".join(printed)
assert target == saved["target_digest"] and len(target) == 128

seen_numbers, seen_files, match_sha, match_b2 = set(), set(), [], []
for entry in plan["candidates"]:
    path = ROOT / entry["path"]
    data = path.read_bytes()
    assert entry["source_number"] not in seen_numbers and entry["path"] not in seen_files
    seen_numbers.add(entry["source_number"])
    seen_files.add(entry["path"])
    assert len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"]
    got_sha = hashlib.sha512(data).hexdigest()
    got_b2 = hashlib.blake2b(data, digest_size=64).hexdigest()
    assert (got_sha, got_b2) == (entry["source_sha512"], entry["source_blake2b"])
    if got_sha == target:
        match_sha.append(entry["path"])
    if got_b2 == target:
        match_b2.append(entry["path"])
assert seen_numbers == {f"{i:02d}" for i in range(75)}
assert len(seen_files) == saved["candidate_count"] == 75
assert match_sha == saved["target_matches"]["sha512"] == []
assert match_b2 == saved["target_matches"]["blake2b512"] == []
assert saved["tested_digests"] == 150

planted_sha = hashlib.sha512((ROOT / "images/lp1-00.jpg").read_bytes()).hexdigest()
planted_b2 = hashlib.blake2b((ROOT / "images/lp1-00.jpg").read_bytes(), digest_size=64).hexdigest()
assert [x["path"] for x in plan["candidates"] if x["source_sha512"] == planted_sha] == ["images/lp1-00.jpg"]
assert [x["path"] for x in plan["candidates"] if x["source_blake2b"] == planted_b2] == ["images/lp1-00.jpg"]
assert saved["positive_controls"] == {"sha512_image00_recovered": ["images/lp1-00.jpg"],
                                      "blake2b_image00_recovered": ["images/lp1-00.jpg"]}
print("PASS: independent target transcription, 75 exact-byte JPEGs, both full digests and two planted lookups")
