"""Write the isolated draft manifest with declared file hashes."""
from __future__ import annotations

import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "experiments/records/wulfic-separator-clock-alberti/"


def row(name: str) -> dict:
    path = HERE / name
    return {"path": BASE + name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main() -> None:
    inputs = ["plan.json", "snapshot_inputs.py", "core.py", "gate.py", "run.py", "check.py", "plot.py", "make_record.py", "article.md"]
    outputs = ["inputs.json", "gate_results.json", "results.json", "comparison.svg"]
    pages = ["lp2-11", "lp2-03", "lp2-04", "lp2-05", "lp2-10", "lp2-12", "lp2-13", "lp2-23", "lp2-24", "lp2-25", "lp2-26"]
    data = {
        "id": "wulfic-separator-clock-alberti",
        "status": "draft",
        "title": "A rotating alphabet with a separator clock",
        "question": "Does the archived two-clock progressive alphabet reach its own frequency gate on its named LP2 targets?",
        "reader_question": "Could the word separators tell a rotating alphabet when to turn?",
        "summary": "No source-selected LP2 page reaches the archived program's 1.4 IoC gate under either its literal parser or a declared corrected-rune variant.",
        "finding": "Across eleven actual LP2 targets, all 1,682 distinct effective schedules per page yield zero outputs above the source's normalized-IoC 1.4 gate with either parser. The highest LP2 values are 1.164 (literal parser) and 1.159 (canonical correction). The source's twelfth named page is solved LP1-15; its literal parser yields two gated outputs but its corrected parser yields none. Eight known-reading plants recover and pass the gate; none of 49 whole-search page-shuffle controls passes either.",
        "limitations": "The source parser omits canonical ᛄ; corrected parsing is a new bounded variant rather than unchanged historical execution. Its old page 15 is solved LP1-15 and excluded from the unsolved-page maximum. The 49 shuffles provide no calibrated probability with zero gated maxima. No plaintext language, phase, extra layer or changing-alphabet family is ruled out.",
        "next_steps": "A new separator-clock proposal should state its glyph parser and page identities, and predict a readable held-out passage before tuning further shifts.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "Alberti", "progressive shift", "separator clock", "input correction"],
        "scope": {
            "pages": pages,
            "artifacts": [BASE + "plan.json"],
            "representation": "Pinned old Wulfic page files with exact source parser and a separate canonical-GP rune correction. Old page15 is solved LP1-15 control only.",
            "procedure": "Enumerate all source directions, two shifts and three modes, deduplicate 5,046 named settings to 1,682 effective outputs, score source normalized IoC and above-gate bigrams/trigrams on each of eleven LP2 targets. Repeat complete search on 49 pagewise shuffled controls for each parser.",
            "parameters": "11 LP2 pages plus one solved LP1 source target; 2 parsers; 29 rune shifts × 29 separator shifts × 2 directions × 3 modes; 49 complete-search shuffles; seed 330123.",
            "exclusions": "Other source pages, nonzero start phase, new separator rules, key switching, other alphabets, extra encryption layers and general Alberti disk mechanisms."
        },
        "review": {"kind": "source-defined finite grid and declared corrected-parser sensitivity", "retested_on": "2026-10-23", "reviewer": "24 source/adapter parity cases, eight recovered known-reading plants, independent reconstruction of 24 observed page and 98 whole-search control results", "human_review": "pending"},
        "reproduction": {"command": "python experiments/records/wulfic-separator-clock-alberti/check.py", "environment": "Python 3 and NumPy; full source-parity gate also requires the pinned Wulfic checkout.", "script": BASE + "check.py", "script_sha256": row("check.py")["sha256"], "inputs": [row(n) for n in inputs], "outputs": [row(n) for n in outputs]},
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Every LP2 page's best two-clock collision score remains below the archived source's 1.4 hit threshold."}],
        "sources": [{"label": "Pinned Wulfic two-clock solver", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/lfsr_alberti_solver.py"}, {"label": "Pinned legacy input warning", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/legacy/README.md"}],
        "related": ["wholepage-progressive-caesar", "alberti-branch-arithmetic", "wulfic-lfsr-singleton-constraints"]
    }
    (HERE / "record.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
