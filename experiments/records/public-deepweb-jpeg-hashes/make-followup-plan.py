"""Freeze the separate 58-file seventh-onion follow-up before target lookup."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = "exports/sources/cicada-2014-seventh-onion/"
manifest_path = BASE + "manifest.json"
audit_path = "exports/cicada-2014-seventh-onion.json"
manifest_raw = (ROOT / manifest_path).read_bytes()
audit_raw = (ROOT / audit_path).read_bytes()
manifest = json.loads(manifest_raw)
audit = json.loads(audit_raw)
assert manifest["revision"] == audit["source_revision"] == "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
assert len(audit["pages"]) == 58
by_file = {item["file"]: item for item in manifest["files"]}
candidates = []
for number in range(58):
    name = f"{number}.jpg"
    path = BASE + name
    raw = (ROOT / path).read_bytes()
    source = by_file[name]
    audited = audit["pages"][number]
    assert audited["page"] == f"lp2-{number:02d}" and audited["archived_path"] == path
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == source["sha256"] == audited["archived_sha256"]
    assert len(raw) == source["bytes"] == audited["archived_bytes"]
    candidates.append({"page": audited["page"], "path": path, "bytes": len(raw),
                       "sha256": digest, "source_url": source["source_url"]})

plan = {
    "schema": "liberpedia-deepweb-seventh-onion-followup-plan-v1",
    "frozen_before_target_comparison": "2026-10-23",
    "relationship_to_primary": "A distinct byte set, not the 75 JPEGs in the Failed-Attempts source table. Its results must be reported separately.",
    "source_repository": "https://github.com/neuroretransmit/cicada",
    "source_revision": manifest["revision"],
    "source_manifest": {"path": manifest_path, "sha256": hashlib.sha256(manifest_raw).hexdigest()},
    "existing_image_audit": {"path": audit_path, "sha256": hashlib.sha256(audit_raw).hexdigest()},
    "target_input": {"path": "data/pages/lp2-56.json", "sha256": hashlib.sha256((ROOT / "data/pages/lp2-56.json").read_bytes()).hexdigest()},
    "question": "Do full-file SHA-512 or BLAKE2b-512 digests of the 58 preserved seventh-onion JPEG bytes equal the LP2-56 target?",
    "algorithms": ["SHA-512", "BLAKE2b-512"],
    "input_rule": "Hash each exact archived JPEG file as bytes with no image decoding, normalization or concatenation; extract LP2-56's five literal hex rows exactly as in the primary record.",
    "positive_control": "Use the computed SHA-512 and BLAKE2b-512 digests of archived 0.jpg as planted targets; each lookup must recover that file uniquely.",
    "limits": "The preservation repository is a source snapshot, not independently authenticated creator-original bytes. This is a follow-up baseline, not a replay of the Failed-Attempts 75-file input set.",
    "candidates": candidates,
}
(HERE / "followup-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"FROZEN: {len(candidates)} archived JPEGs; SHA-256 {hashlib.sha256((HERE / 'followup-plan.json').read_bytes()).hexdigest()}")
