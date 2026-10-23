"""Write publication metadata with hashes of all 75 declared JPEG inputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = "public-deepweb-jpeg-hashes"
PRE = f"experiments/records/{ID}/"


def entry(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


plan = json.loads((HERE / "plan.json").read_bytes())
image_paths = [x["path"] for x in plan["candidates"]]
assert len(image_paths) == len(set(image_paths)) == 75
followup = json.loads((HERE / "followup-plan.json").read_bytes())
archived_paths = [x["path"] for x in followup["candidates"]]
assert len(archived_paths) == len(set(archived_paths)) == 58
record = {
    "id": ID,
    "status": "draft",
    "title": "Do the manuscript JPEGs hash to the deep-web target?",
    "question": "Does full-file SHA-512 or BLAKE2b-512 of the 75 source JPEGs, or a separately pinned 58-file archive, equal the LP2-56 target?",
    "reader_question": "Have we tried hashing the manuscript images against LP2-56?",
    "summary": "The published 75-image source set is recovered exactly and has no target match. A separately pinned 58-image seventh-onion byte set also has no target match under the same two algorithms.",
    "finding": "All 75 source JPEGs match both digest columns in the pinned source checksum table; none of 150 full-file digests equals the LP2-56 target. In a distinct follow-up, none of 116 digests from 58 preserved seventh-onion JPEGs matches either. Separate planted image-00 targets are recovered for both sets and algorithms.",
    "limitations": "These are two specified file sets, not one historical source run: the 75-file set replays Failed-Attempts, while the 58-file seventh-onion check is a new bounded follow-up. Neither preserved set is independently authenticated as creator-original bytes. Other files, transforms, combinations and hash interpretations remain untested.",
    "next_steps": "A different target proposal should specify its candidate bytes and transformation before comparing the hash, so a negative result has a defined scope.",
    "outcome": "not-supported",
    "tags": ["LP2-56", "deep web", "SHA-512", "BLAKE2b", "JPEG", "public-source replay", "file provenance"],
    "related": [],
    "scope": {
        "pages": ["lp2-56"],
        "artifacts": [PRE + "plan.json", PRE + "followup-plan.json", "data/pages/lp2-56.json", "exports/sources/cicada-2014-seventh-onion/manifest.json", "exports/cicada-2014-seventh-onion.json"],
        "representation": "Two explicitly separate exact-byte sets: 75 hosted LP1+LP2 JPEGs identified by the Failed-Attempts checksum table, and 58 preserved seventh-onion LP2 JPEGs identified by a pinned archive manifest.",
        "procedure": "Freeze both candidate sets separately before target comparison; hash full files with SHA-512 and BLAKE2b-512; join LP2-56's five printed hex lines; compare 150 source-replay digests and 116 follow-up digests without combining their results. Independently rehash and plant a known image-00 target in both sets.",
        "parameters": "75 source images plus 58 distinct archived images, each under two fixed 512-bit algorithms, one exact 128-hex LP2-56 target; no adjustable key, transform or substring search.",
        "exclusions": "Re-exports or crops beyond the two pinned sets, concatenated or embedded file data, other web pages, other hash algorithms and claims about LP2's runic cipher."
    },
    "review": {
        "reviewer": "Independent raw-page transcription and full-file digest checkers for both pinned sets, 150 source digest matches and four planted controls",
        "retested_on": "2026-10-23",
        "kind": "computational source replay",
        "human_review": "pending"
    },
    "reproduction": {
        "command": "python experiments/records/public-deepweb-jpeg-hashes/run.py --check && python experiments/records/public-deepweb-jpeg-hashes/check.py && python experiments/records/public-deepweb-jpeg-hashes/followup.py --check && python experiments/records/public-deepweb-jpeg-hashes/followup-check.py",
        "environment": "Python 3 offline. Use the complete repository checkout, or extract this experiment ZIP together with Original images (ZIP) so both declared images/ and exports/sources/cicada-2014-seventh-onion/ paths exist.",
        "script": PRE + "run.py",
        "script_sha256": entry(PRE + "run.py")["sha256"],
        "inputs": [entry(path) for path in [PRE + "plan.json", PRE + "make_plan.py", PRE + "check.py", PRE + "followup-plan.json", PRE + "make-followup-plan.py", PRE + "followup.py", PRE + "followup-check.py", PRE + "make_record.py", "data/pages/lp2-56.json", "exports/sources/cicada-2014-seventh-onion/manifest.json", "exports/cicada-2014-seventh-onion.json", *image_paths, *archived_paths]],
        "outputs": [entry(PRE + "results.json"), entry(PRE + "followup-results.json"), entry(PRE + "source-hash-check.svg")]
    },
    "sources": [
        {"label": "Pinned Failed-Attempts hash-lookup method and checksum table", "url": "https://github.com/LiberPrimus/Failed-Attempts/tree/d219a8099f8d24e52496e9ee3456ed9980893884/deepweb-hash"},
        {"label": "Preserved seventh-onion JPEG source", "url": "https://github.com/neuroretransmit/cicada/tree/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2014/011-seventh-onion"}
    ],
    "visuals": [{"path": PRE + "source-hash-check.svg", "caption": "The 75-file source replay and separate 58-file seventh-onion follow-up each have zero matches to LP2-56 under two full-file hash algorithms."}]
}
(HERE / "record.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
