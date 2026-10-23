"""Independent check of the distinct seventh-onion JPEG follow-up."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan_raw = (HERE / "followup-plan.json").read_bytes()
plan = json.loads(plan_raw)
saved = json.loads((HERE / "followup-results.json").read_bytes())
assert hashlib.sha256(plan_raw).hexdigest() == saved["followup_plan_sha256"]
for item in (plan["source_manifest"], plan["existing_image_audit"], plan["target_input"]):
    assert hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() == item["sha256"]
manifest = json.loads((ROOT / plan["source_manifest"]["path"]).read_bytes())
assert manifest["revision"] == saved["source_revision"]
source_items = {f["file"]: f for f in manifest["files"]}

page = json.loads((ROOT / plan["target_input"]["path"]).read_bytes())
assert page["id"] == "lp2-56"
hex_rows = [line["raw"].rstrip("/") for line in page["lines"]
            if re.fullmatch(r"[0-9a-f]{20,32}/?", line["raw"])]
assert len(hex_rows) == 5
target = "".join(hex_rows)
assert len(target) == 128 and target == saved["target_digest"]

primary = json.loads((HERE / "plan.json").read_bytes())
source_sha = {x["source_sha512"] for x in primary["candidates"]}
source_b2 = {x["source_blake2b"] for x in primary["candidates"]}
got = []
for index, item in enumerate(plan["candidates"]):
    assert item["page"] == f"lp2-{index:02d}"
    assert item["path"].endswith(f"/{index}.jpg")
    meta = source_items[f"{index}.jpg"]
    raw = (ROOT / item["path"]).read_bytes()
    assert len(raw) == item["bytes"] == meta["bytes"]
    assert hashlib.sha256(raw).hexdigest() == item["sha256"] == meta["sha256"]
    got.append({"page": item["page"], "path": item["path"],
                "sha512": hashlib.sha512(raw).hexdigest(),
                "blake2b512": hashlib.blake2b(raw).hexdigest()})
assert len(got) == saved["candidate_count"] == 58
assert got == saved["digests"]
assert saved["tested_digests"] == 116
assert saved["matches_sha512"] == [x["path"] for x in got if x["sha512"] == target] == []
assert saved["matches_blake2b512"] == [x["path"] for x in got if x["blake2b512"] == target] == []
assert saved["digest_overlap_with_primary_source_set"] == {
    "sha512": sum(x["sha512"] in source_sha for x in got),
    "blake2b512": sum(x["blake2b512"] in source_b2 for x in got)} == {"sha512": 0, "blake2b512": 0}
assert saved["positive_controls"] == {
    "sha512_archive0_recovered": [x["path"] for x in got if x["sha512"] == got[0]["sha512"]],
    "blake2b_archive0_recovered": [x["path"] for x in got if x["blake2b512"] == got[0]["blake2b512"]]}
assert saved["positive_controls"] == {
    "sha512_archive0_recovered": [got[0]["path"]],
    "blake2b_archive0_recovered": [got[0]["path"]]}
print("PASS: independent source manifest, 58 exact archived bytes, 116 digests and planted lookups")
