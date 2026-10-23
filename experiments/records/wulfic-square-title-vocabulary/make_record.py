"""Refresh Stage I title-only metadata and dependency hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main() -> None:
    inputs = [BASE + x for x in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                  "make_record.py", "source-title-output.txt")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "LP2-15 square-derived title keys",
        "question": "Do five specified number sequences from the LP2-15 square turn its nine-rune heading into two complete words under fixed GP29 arithmetic?",
        "reader_question": "Does the LP2-15 square decode its short heading?",
        "summary": "Exact Stage I title replay checks 30 complete two-word outputs from five square-derived key sequences, both directions and three arithmetic signs; none passes the source vocabulary gate.",
        "finding": "The pinned source reports 0/30 complete two-word vocabulary passes. Its 20,000 seeded random nine-rune subtraction keys also yield zero passes. Independent site-text arithmetic reproduces every candidate output; optional full source replay reproduces the vocabulary verdicts and control byte-for-byte.",
        "limitations": "A strict vocabulary miss for these 30 fixed candidates cannot exclude other square routes, shifts, spelling conventions, keys, vocabularies or a different cipher on the LP2-15 body. Zero hits in 20,000 random keys does not mean a zero chance probability.",
        "next_steps": "A new square-title proposal should fix its traversal, key conversion, arithmetic and full two-word prediction before checking the heading, then make an additional prediction beyond those nine runes.",
        "outcome": "not-supported",
        "tags": ["LP2-15", "source replay", "number square", "Fibonacci", "title crib", "search bounds"],
        "scope": {
            "pages": ["lp2-15"], "artifacts": [BASE + "source-title-output.txt"],
            "representation": "First nine archived LP2-15 runes with the visible 4+5 word boundary, and its printed 16-value number square. GP29 zero-based indices.",
            "procedure": "Run only the pinned Stage I title function; independently derive all five 16-value sequences, compare the constructed cell-value set with the printed panel and recalculate all 30 two-word outputs from Liberpedia page text.",
            "parameters": "Five declared sequences x outward/inward x ciphertext-key, ciphertext+key and key-ciphertext, modulo 29; first nine key values; complete two-word vocabulary gate; 20,000 seeded random-key controls.",
            "exclusions": "Alternate source routes, key starts, body text, vocabulary, GP spelling, punctuation choices and additional cipher layers."
        },
        "review": {
            "kind": "exact public-source Stage I title-function replay with independent site-text arithmetic",
            "retested_on": "2026-10-23",
            "reviewer": "Thirty decoded pairs independently reproduced; pinned source title output including 20,000-key control reproduced byte-for-byte",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Bundled checks use Python 3 standard library. Optional vocabulary/control replay needs NumPy and the external pinned source checkout.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(x) for x in inputs],
            "outputs": [hashed(BASE + x) for x in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Five source number sequences, two directions and three arithmetic rules produce 30 complete heading candidates; none passes the source's two-word vocabulary gate."}],
        "sources": [
            {"label": "Pinned Wulfic Stage I source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_i.py"},
            {"label": "Pinned square construction", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/lpcore/stats.py"},
        ],
        "related": ["wulfic-native-key-streams", "lp2-15-totient-gap-audit", "lp2-15-mobius-panel"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
