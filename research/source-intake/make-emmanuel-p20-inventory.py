"""Build an exact internal method/file inventory of a pinned external checkout."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2] / "sources" / "emmanuel-p20-lf"
REVISION = "a39e7de90ff9414791fe5f4f8d44540bd0bdb089"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), *args])


assert git("rev-parse", "HEAD").decode().strip() == REVISION
names = git("ls-files", "-z").decode("utf-8").rstrip("\0").split("\0")
files = []
for name in names:
    raw = git("show", f"{REVISION}:{name}")
    files.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)})

manifest_rows = git("show", f"{REVISION}:MANIFEST_SHA256.tsv").decode("utf-8").splitlines()[1:]
manifest = {path: digest for digest, path in (line.split("\t", 1) for line in manifest_rows)}
indexed = {file["path"]: file for file in files}
missing = sorted(set(manifest) - set(indexed))
mismatch = sorted(path for path in manifest if path in indexed and manifest[path] != indexed[path]["sha256"])

groups = {
    "finite boundary test and calibration": [33, 35, 38, 40],
    "exception and 272 branch checks": [43, 44, 45, 46, 48, 54],
    "atlas geometry and state checks": [56, 58, 61, 62, 63, 66],
    "plaintext/status and source-limit accounting": [72, 71, 73, 76],
}
number_to_group = {number: group for group, numbers in groups.items() for number in numbers}
active = []
run_full = git("show", f"{REVISION}:analysis/run_full.py").decode("utf-8")
for path in names:
    if not path.startswith("analysis/") or not path.endswith(".py"):
        continue
    tail = Path(path).name
    if len(tail) < 3 or not tail[:2].isdigit() or tail[2] != "_":
        continue
    number = int(tail[:2])
    result_path = path[:-3] + ".json"
    active.append({"script": path, "saved_result": result_path if result_path in indexed else None,
                   "group": number_to_group.get(number, "outside declared active groups"),
                   "in_run_full": f"'{tail}'" in run_full})

data = {
    "schema": "liberpedia-public-repo-file-method-intake-v1",
    "source_url": "https://github.com/emmanuel6474/liber-primus-p20-analysis",
    "revision": REVISION,
    "commit_url": f"https://github.com/emmanuel6474/liber-primus-p20-analysis/tree/{REVISION}",
    "scope": "Exact Git tree/file and executable inventory. Source conclusions remain claims until their individual input, method and outputs are checked.",
    "tracked_file_count": len(files),
    "tracked_files": files,
    "license": "No LICENSE file or other explicit license was found in the pinned Git tree; do not redistribute source code or data as a Liberpedia bundle.",
    "source_manifest": {
        "path": "MANIFEST_SHA256.tsv",
        "listed_count": len(manifest),
        "missing_from_git_tree": missing,
        "present_hash_mismatches_against_git_blobs": mismatch,
        "quick_verifier_consequence": "python verify.py fails at the missing .github/workflows/verify.yml even with byte-preserving LF checkout. Windows core.autocrlf=true additionally changes 83 tracked text-file working bytes, but their Git blob hashes match the manifest."
    },
    "method_groups": groups,
    "method_inventory": active,
    "raw_workspace_limit": "Original twosided_data.h, rank_data.h, broad_data.h, candidate_check.py, exception_fit.py, decode_272_allpout.py and unified_dynamic_fit.py are absent; upstream START/272 outputs cannot be regenerated from original raw arrays here.",
    "bounded_replay": {
        "source_scripts": ["analysis/33_boundary_complete_crossvalidation.py",
                           "analysis/35_exact_null_independent_verifier.py",
                           "analysis/38_positive_control_plant_and_recover.py"],
        "input": "analysis/evidence/boundary_numeric_evidence.json",
        "input_sha256": indexed["analysis/evidence/boundary_numeric_evidence.json"]["sha256"],
        "replayed_on": "2026-10-23",
        "observed": "34,020 supplied state assignments; zero global fits in six declared sub-saturated joint affine model classes; five in saturated 6/6; exact conditioned c18 P(hits>=5)=0.5523905497673823; two planted low-complexity laws recovered and mutated controls rejected.",
        "source_output_semantic_match": True,
        "limit": "This replay is conditional on the bundled normalized numeric evidence. It cannot independently derive those menus or features from the missing historical raw workspace, and it does not decode a page."
    }
}
out = HERE / "emmanuel-p20-a39e7de.json"
out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
print(out, len(files), len(active), missing, mismatch)
