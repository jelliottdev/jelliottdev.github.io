"""Refresh hashes and draft metadata for the Stage X2 source replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


if __name__ == "__main__":
    artifact = BASE + "source-stage_x_periodic.tsv"
    inputs = [BASE + name for name in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                      "make_record.py", "source-stage_x_periodic.tsv")]
    inputs += ["exports/alphanumeric-grids.csv"]
    record = {
        "id": HERE.name,
        "status": "draft",
        "title": "Repeating-byte-alphabet invariant on the LP2 grid",
        "question": "Do equal-byte pairs in the LP2 grid support a periodically repeated one-to-one byte alphabet?",
        "reader_question": "Could a repeating byte alphabet explain the number grid?",
        "summary": "Exact Stage X2 replay checks both grid routes and every period 1–128. No period exceeds the uniform-null maximum; conditional plaintext-control exclusions range from 78 to 247 of 256 cells.",
        "finding": "No grid reading/period cell exceeds the maximum of 100,000 uniform-byte nulls. Under the source's lower 0.1% control rule, 241/256 cells are excluded for Emerson English, 247/256 for solved LP1 runes, 247/256 for HEX, and 78/256 for Base64. No decoding is produced.",
        "limitations": "The exclusions require a fixed bijection at each periodic residue and the source's exact plaintext-control classes and 256-byte representation. Other grid routes, transformations, layered ciphers and plaintext distributions remain outside scope.",
        "next_steps": "A proposed surviving period needs a specified key, decoding rule and held-out check. Alternate byte routes or control classes require their own declared test and controls.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "number grid", "periodic substitution", "byte equality", "search bounds"],
        "scope": {
            "pages": ["lp2-49", "lp2-50", "lp2-51"],
            "artifacts": [artifact],
            "representation": "The 256 printed grid tokens as base-60 bytes, traversed in printed 32×8 row order or column-major order.",
            "procedure": "Replay only pinned Wulfic Stage X2 and independently reconstruct all 256 grid coincidence counts, pair capacities and source decisions; verify a planted residue-bijection invariant.",
            "parameters": "Two readings × periods 1–128; 100,000 seeded uniform-null blocks; 9,024 Emerson, 2,646 solved-LP1, 10,000 HEX and 10,000 Base64 256-byte controls; source upper-maximum and lower-0.1%-quantile rules.",
            "exclusions": "Other traversal routes, offsets, payload extraction, compression, non-bijective or changing alphabets, transposition, layered ciphers, and Stage X1/X3/X4 tests."
        },
        "review": {
            "kind": "exact public-source Stage X2 replay with independent complete grid-row check",
            "retested_on": "2026-10-23",
            "reviewer": "Pinned source table reproduced byte-for-byte; 256 site-grid counts and decisions independently checked; mathematical planted controls passed",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python " + BASE + "run.py --check && python " + BASE + "plot.py --check",
            "environment": "Bundled verification uses Python 3 standard library. The optional full pinned-source replay needs NumPy and the external checkout.",
            "script": BASE + "run.py",
            "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(path) for path in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Conditional exclusions by plaintext-control class among 256 grid-reading/period cells. No cell had the source's positive structural signal."}],
        "sources": [
            {"label": "Wulfic Stage X at pinned revision",
             "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_x.py"},
            {"label": "Pinned source grid construction",
             "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/keys.py"}
        ],
        "related": ["grid-direct-bytes", "rune-direct-compression"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
