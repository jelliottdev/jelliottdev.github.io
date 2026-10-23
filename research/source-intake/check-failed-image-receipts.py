"""Compare the pinned Failed-Attempts JPEG checksum table with local archived sets."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "sources/failed-attempts-d219a8/deepweb-hash/checksums.txt"
rows = re.findall(r"^/(\d+)\.jpg SHA512:\s+([0-9a-f]{128})", SOURCE.read_text(), re.M)
assert len(rows) == 75
expected = {digest: number for number, digest in rows}
groups = {
    "hosted75": sorted((ROOT / "images").glob("lp[12]-*.jpg")),
    "archived58": sorted((ROOT / "exports/sources/cicada-2014-seventh-onion").glob("[0-9]*.jpg")),
}
report = {"schema": "liberpedia-failed-attempts-jpeg-receipt-audit-v1", "source_table": str(SOURCE), "groups": {}}
for name, files in groups.items():
    matches = []
    for path in files:
        digest = hashlib.sha512(path.read_bytes()).hexdigest()
        if digest in expected:
            matches.append({"local_path": str(path.relative_to(ROOT)).replace("\\", "/"), "source_number": expected[digest]})
    report["groups"][name] = {"candidate_count": len(files), "sha512_matches": len(matches), "matches": matches}
print(json.dumps(report, indent=2))
