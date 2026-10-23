"""Pin exact upstream Git blobs before running the conditional source replay."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "sources" / "emmanuel-p20-lf"
REVISION = "a39e7de90ff9414791fe5f4f8d44540bd0bdb089"
assert subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"]).decode().strip() == REVISION


def blob(path: str) -> dict[str, str]:
    raw = subprocess.check_output(["git", "-C", str(SOURCE), "show", f"{REVISION}:{path}"])
    return {"path": path, "sha256": hashlib.sha256(raw).hexdigest()}


required = ["analysis/evidence/boundary_numeric_evidence.json",
            "analysis/33_boundary_complete_crossvalidation.py",
            "analysis/35_exact_null_independent_verifier.py",
            "analysis/38_positive_control_plant_and_recover.py",
            "analysis/33_boundary_complete_crossvalidation.json",
            "analysis/35_exact_null_independent_verifier.json",
            "analysis/38_positive_control_plant_and_recover.json",
            "MANIFEST_SHA256.tsv", "PROVENANCE.md", "NEGATIVE_RESULTS.md"]
plan = {
    "schema": "liberpedia-public-p20-static-boundary-plan-v1",
    "frozen_before_local_replay": "2026-10-23",
    "source_url": "https://github.com/emmanuel6474/liber-primus-p20-analysis",
    "source_revision": REVISION,
    "question": "Do the pinned repository's eight supplied P20 boundary state menus reproduce its finite GF(83) static-affine fit counts and its exact saturated null comparison?",
    "source_scope": "Eight normalized numeric boundary contexts in the repository's source-defined 812-rune P20 section; not a fresh derivation from the missing upstream raw workspace or a whole-page decryption.",
    "operations": "Run upstream scripts 33, 35 and 38 from exact pinned Git blobs in an isolated temporary directory against the exact pinned numeric evidence. Script 33 enumerates 34,020 admissible state assignments and the declared joint feature-count classes over GF(83). Script 35 independently checks the fit counts and computes the conditioned c18 null exactly. Script 38 plants two known four-feature affine laws and mutates a target as a negative control.",
    "acceptance": "Each source script must exit successfully, regenerated JSON must equal its committed JSON object semantically, and the declared 34,020 / 0 sub-saturated / 5 saturated / p=0.5523905497673823 / planted-control outcomes must hold. Source byte-level output hashes can differ on Windows due newline translation; input and code Git blobs must match SHA-256.",
    "license_and_reproduction": "The pinned Git tree has no explicit LICENSE. Liberpedia links to and verifies the pinned source; it does not redistribute that repository's code or normalized input. Reproduction requires a local clone at the exact revision, supplied to --source.",
    "provenance_limit": "The source repository omits its historical raw workspace (including original solver arrays); the replay is conditional on the bundled normalized numeric evidence. It cannot establish that the input menus were independently obtained from LP2 or that the proposal decodes any page.",
    "manifest_issue": "MANIFEST_SHA256.tsv lists .gitignore and .github/workflows/verify.yml, neither in the pinned Git tree. Its quick verify.py therefore fails on the missing workflow file; the mathematical scripts are run individually instead.",
    "source_files": [blob(path) for path in required],
    "local_inputs": [
        {"path": "research/source-intake/emmanuel-p20-a39e7de.json",
         "sha256": hashlib.sha256((ROOT / "research/source-intake/emmanuel-p20-a39e7de.json").read_bytes()).hexdigest()}
    ]
}
(HERE / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
