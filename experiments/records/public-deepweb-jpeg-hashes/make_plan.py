"""Freeze the exact 75-source-JPEG input set before comparing with the LP2-56 target."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "sources/failed-attempts-d219a8"
REV = "d219a8099f8d24e52496e9ee3456ed9980893884"
assert subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"]).decode().strip() == REV
def blob(path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(SOURCE), "show", f"{REV}:{path}"])

table_raw = blob("deepweb-hash/checksums.txt")
table = table_raw.decode("utf-8")
sha = dict(re.findall(r"^/(\d+)\.jpg SHA512:\s+([0-9a-f]{128})", table, re.M))
b2 = dict(re.findall(r"^/(\d+)\.jpg BLAKE2:\s+([0-9a-f]{128})", table, re.M))
assert len(sha) == len(b2) == 75 and set(sha) == set(b2) == {f"{i:02d}" for i in range(75)}

files = []
for ordinal in range(75):
    number = f"{ordinal:02d}"
    name = f"lp1-{ordinal:02d}" if ordinal < 17 else f"lp2-{ordinal - 17:02d}"
    rel = f"images/{name}.jpg"
    raw = (ROOT / rel).read_bytes()
    assert hashlib.sha512(raw).hexdigest() == sha[number], f"Source SHA-512 mismatch for {rel}"
    assert hashlib.blake2b(raw).hexdigest() == b2[number], f"Source BLAKE2b mismatch for {rel}"
    files.append({"source_number": number, "path": rel, "bytes": len(raw),
                  "sha256": hashlib.sha256(raw).hexdigest(),
                  "source_sha512": sha[number], "source_blake2b": b2[number]})

plan = {
    "schema": "liberpedia-public-deepweb-jpeg-hashes-plan-v1",
    "frozen_before_target_comparison": "2026-10-23",
    "source_url": "https://github.com/LiberPrimus/Failed-Attempts",
    "source_revision": REV,
    "source_readme_sha256": hashlib.sha256(blob("deepweb-hash/README.md")).hexdigest(),
    "source_script_sha256": hashlib.sha256(blob("deepweb-hash/checksums.sh")).hexdigest(),
    "source_checksum_table_sha256": hashlib.sha256(table_raw).hexdigest(),
    "question": "Does either full-file SHA-512 or BLAKE2b-512 of any of the exact 75 JPEGs in the pinned source checksum table equal the LP2-56 128-hex target?",
    "target_input": {"path": "data/pages/lp2-56.json",
                     "sha256": hashlib.sha256((ROOT / "data/pages/lp2-56.json").read_bytes()).hexdigest()},
    "algorithm_rules": "Hash exact JPEG bytes, no image decoding or normalization. SHA-512 and BLAKE2b-512 use full 128-hex digests. Extract and join the five printed hexadecimal rows from LP2-56, removing only row-end slashes.",
    "positive_control": "Replace the lookup target with the computed SHA-512 and BLAKE2b-512 of source image 00; each algorithm must recover exactly that image.",
    "candidate_scope": "All 75 JPEGs whose complete SHA-512 and BLAKE2b-512 digests match the pinned Failed-Attempts table, mapped in source ordinal order to hosted LP1-00–16 and LP2-00–57 files.",
    "exclusions": "No alternate byte encodings, image re-exports, concatenated files, cropped image data, arbitrary web pages or other hash algorithms. The 58 archived seventh-onion JPEGs are a distinct byte set and not part of the source-exact replay.",
    "candidates": files,
}
HERE.mkdir(parents=True, exist_ok=True)
(HERE / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"FROZEN: {len(files)} JPEGs; SHA-256 {hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest()}")
