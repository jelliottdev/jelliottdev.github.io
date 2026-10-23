"""Write the reviewed record with hashes of all local reproduction files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = "public-p20-static-boundary"
PREFIX = f"experiments/records/{ID}/"


def entry(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


record = {
    "id": ID,
    "status": "draft",
    "title": "A bounded test of the P20 boundary model",
    "question": "Do the supplied numeric P20 boundary states support a single static affine rule modulo 83?",
    "reader_question": "Has the proposed P20 static boundary rule been checked?",
    "summary": "The pinned source's finite calculation reproduces on its bundled numeric menus. Six lower-complexity model classes have no complete fit; five saturated fits are ordinary under its exact conditioned comparison.",
    "finding": "Across 34,020 allowed state-pair assignments at eight contexts, six lower-complexity classes have zero complete fits and the saturated (6,6) class has five. An independent exact calculation gives 4.94 expected and P(at least five)=0.552. Two planted low-complexity laws are recovered exactly.",
    "limitations": "The original raw workspace is absent. We did not independently derive the eight numeric menus or feature vectors from LP2, and this conditional replay does not decode a page or exclude dynamic boundary rules. The pinned source's manifest also names two absent files, so its quick verifier does not pass.",
    "next_steps": "Recover or independently reconstruct the raw section data and state-menu extraction; then test a frozen rule on held-out manuscript boundaries.",
    "outcome": "inconclusive",
    "tags": ["public-source replay", "boundary states", "static affine model", "GF83", "exact null", "source provenance"],
    "related": [],
    "scope": {
        "pages": [],
        "artifacts": ["research/source-intake/emmanuel-p20-a39e7de.json", PREFIX + "plan.json"],
        "representation": "Eight source-supplied numeric boundary contexts for an 812-rune section named P20 by the external repository; no asserted mapping to one Liberpedia page.",
        "procedure": "Verify pinned Git blobs, execute source scripts 33, 35 and 38 in isolation, compare regenerated JSON objects, and independently calculate the menu product and exact conditioned tail.",
        "parameters": "34,020 assignments; seven joint feature-count classes over GF(83), including saturated (6,6); conditioned c18 menu of nine state pairs; two planted affine laws plus one-value mutations.",
        "exclusions": "Original raw-data derivation, all other static or dynamic state models, independent manuscript decryption, and other sections of LP2."
    },
    "review": {
        "reviewer": "Pinned Git-blob replay, semantic result comparison, separate exact arithmetic checker and planted controls",
        "retested_on": "2026-10-23",
        "kind": "computational source replay",
        "human_review": "pending"
    },
    "reproduction": {
        "command": "python experiments/records/public-p20-static-boundary/run.py --source PATH_TO_SOURCE_CLONE --check && python experiments/records/public-p20-static-boundary/check.py --source PATH_TO_SOURCE_CLONE",
        "environment": "Python 3 and Git. Clone external source at pinned commit a39e7de90ff9414791fe5f4f8d44540bd0bdb089 and supply its path; no external source code is bundled.",
        "script": PREFIX + "run.py",
        "script_sha256": entry(PREFIX + "run.py")["sha256"],
        "inputs": [entry(path) for path in [PREFIX + "plan.json", PREFIX + "make_plan.py", PREFIX + "check.py", PREFIX + "make_record.py", "research/source-intake/emmanuel-p20-a39e7de.json"]],
        "outputs": [entry(path) for path in [PREFIX + "results.json", PREFIX + "boundary-fit.svg"]]
    },
    "sources": [
        {"label": "Pinned P20 analysis repository", "url": "https://github.com/emmanuel6474/liber-primus-p20-analysis/tree/a39e7de90ff9414791fe5f4f8d44540bd0bdb089"},
        {"label": "Repository provenance and missing raw-workspace disclosure", "url": "https://github.com/emmanuel6474/liber-primus-p20-analysis/blob/a39e7de90ff9414791fe5f4f8d44540bd0bdb089/PROVENANCE.md"}
    ],
    "visuals": [{"path": PREFIX + "boundary-fit.svg", "caption": "Finite static-affine fits on the eight supplied numeric contexts and the exact conditioned comparison for five saturated fits."}]
}
(HERE / "record.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
