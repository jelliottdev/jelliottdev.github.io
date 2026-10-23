"""Write draft record with exact declared bytes after the frozen scan."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ID = HERE.name
BASE = f"experiments/records/{ID}/"


def hashed(rel: str) -> dict[str, str]:
    return {"path": rel, "sha256": hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()}


def main() -> None:
    rec = {
        "id": ID,
        "status": "draft",
        "title": "Can single-rune words pin down an LFSR key?",
        "question": "Do source-defined GF(29) linear-feedback streams of lengths one through five make every visible one-rune word on LP2-28, LP2-24 and LP2-21 read I or A?",
        "reader_question": "Can one-rune words reveal the key stream?",
        "summary": "The source's exact I/A singleton constraints admit four five-state Beaufort settings on LP2-28, about 27,400 settings on LP2-24 and 5.8 million on LP2-21. These are crib fits, not readings.",
        "finding": "Across all 29^L feedback tuples for each L=1–5, no selected page has a complete singleton fit at L1–2. At L5, the source's first-L invertible search yields four LP2-28 Beaufort fits, 27,424 combined subtraction/Beaufort fits on LP2-24 and 5,808,457 on LP2-21. Addition has exact signed-state symmetry with subtraction and is not counted again in that comparison. All four LP2-28 full-page example decodes have normalized IoC below the source's 1.3 shortcut; no full-page English selection claim is made.",
        "limitations": "Assumes every visible one-rune word is plaintext I or A, canonical GP indices, page-local continuous key and first-L invertible basis. Singular first-L systems are excluded by the source algorithm. Full-grid dictionary scoring is not calibrated or claimed. Fitting singleton slots does not identify a ciphertext generator or decryption.",
        "next_steps": "Specify a single candidate's taps, starting state, direction, page boundary rule and out-of-crib plaintext prediction before testing additional text.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source-derived test", "LFSR", "one-rune words", "crib constraints", "search bounds"],
        "scope": {
            "pages": ["lp2-21", "lp2-24", "lp2-28"],
            "artifacts": [BASE + "plan.json", BASE + "inputs.json"],
            "representation": "Canonical GP29 page-local rune streams; source parser singleton positions: 12 on LP2-28, 9 on LP2-24, 7 on LP2-21. Pinned archived scan ordinals 45, 41 and 38 separately checked by unchanged source parser.",
            "procedure": "Exhaust feedback tap tuples over GF(29), solve invertible first-L singleton constraints for all I/A assignments, test remaining singletons and decode example full pages exactly; independent small-grid oracle and planted controls.",
            "parameters": "L=1..5; each coefficient 0..28; plaintext I=10 or A=24 at visible one-rune words; sub/add/Beaufort directions; first-L invertible systems only; 29^L tuples per length and target.",
            "exclusions": "Different singleton plaintext, non-GP mapping, page-spanning or skipped clocks, singular source basis, other recurrence families, whole-grid calibrated English verdict and proof of decryption."
        },
        "review": {"kind": "source-defined bounded extension with exact input alignment and independent oracle",
                   "retested_on": "2026-10-23",
                   "reviewer": "15 scanner plants; independent full L1/L2, 100-tuple L3–L5, all 45 rows and full-page examples; post-scan exhaustive small-field oracles and nonconsecutive GF29 plants",
                   "human_review": "pending"},
        "reproduction": {
            "command": f"python {BASE}run.py --check",
            "environment": "Python 3 standard library for saved-output checks; C++17 g++ compiler for the complete exhaustive run.",
            "script": BASE + "check.py",
            "script_sha256": hashed(BASE + "check.py")["sha256"],
            "inputs": [hashed(BASE + n) for n in ("plan.json", "inputs.json", "scan-input.txt", "scan.cpp", "prepare.py", "controls.py", "finalize.py", "run.py", "plot.py", "check_source_input.py")]
                      + [hashed(f"data/pages/lp2-{i:02d}.json") for i in (21, 24, 28)],
            "outputs": [hashed(BASE + n) for n in ("results.json", "full-summary.tsv", "spot-summary.tsv", "control-input.txt", "control-summary.tsv", "control-candidates.tsv", "fits.svg")],
        },
        "visuals": [{"path": BASE + "fits.svg", "caption": "Singleton-crib fits by page and linear-feedback memory length; a fit is not a decoded reading."}],
        "sources": [{"label": "Pinned Wulfic GF(29) LFSR proposal", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/lfsr_gf29_solver.py"},
                    {"label": "Pinned Wulfic legacy trust note", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md"}],
        "related": ["periodic-affine-crib-capacity", "solved-reading-running-key", "wulfic-early-keyspace-diagnostics"]
    }
    (HERE / "record.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
