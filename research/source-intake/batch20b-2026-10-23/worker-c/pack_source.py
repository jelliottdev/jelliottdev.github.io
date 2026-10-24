"""Archive the pinned MIT source dependencies used for the T3 replay."""
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

REV = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
SOURCE_REPO = Path("C:/Users/ianex/Documents/Codex/2026-10-19/i-w/dukotah-audit")
OUT = Path(__file__).resolve().parent / "source-snapshot.zip"
base = "liber-primus/"
paths = [
    "LICENSE",
    *[base + "analysis/round19/T3/" + name for name in (
        "PREREG.md", "RESULTS.md", "t3_lib.py", "t3_baseline.py",
        "t3_sensitivity.py", "t3_targeted.py", "t3_decode.py")],
    *[base + name for name in (
        "analysis/stones/pipeline.py", "analysis/round11/lib_numchannel.py",
        "analysis/run_stats.py", "analysis/campaign18_skip/skipdecode.py",
        "analysis/round18/L2-filter-leak/fastbeam.py",
        "analysis/independent-read/oae_mismatch.json",
        "data/krisyotam_runes.txt", "data/english_quadgrams.txt",
        "SOLVED-PAGES.json", "PROBLEM.json")],
]
lp_tree = subprocess.check_output(
    ["git", "ls-tree", "-r", "--name-only", REV, "liber-primus/src/lp"],
    cwd=SOURCE_REPO, text=True).splitlines()
paths.extend(p for p in lp_tree if p.endswith(".py"))
manifest = {"revision": REV, "files": []}
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name in sorted(set(paths)):
        raw = subprocess.check_output(["git", "show", f"{REV}:{name}"], cwd=SOURCE_REPO)
        info = zipfile.ZipInfo(name, date_time=(2026, 10, 23, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        manifest["files"].append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})
(OUT.parent / "source-snapshot-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"{OUT.name}: {len(manifest['files'])} files, {OUT.stat().st_size} bytes")
