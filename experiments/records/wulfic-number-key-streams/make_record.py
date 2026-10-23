"""Build the metadata with hashes of the actual checked inputs and outputs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = "experiments/records/wulfic-number-key-streams/"


def digest(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


if __name__ == "__main__":
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    inputs = [digest(PREFIX + "plan.json")]
    inputs += [digest(path) for path in (
        PREFIX + "check.py", PREFIX + "plot.py", PREFIX + "replay_source.py",
        PREFIX + "make_plan.py", PREFIX + "make_record.py")]
    inputs += [digest(item["path"]) for item in plan["inputs"]]
    output_paths = [PREFIX + "results.json", PREFIX + "comparison.svg"]
    record = {
        "id": "wulfic-number-key-streams",
        "status": "draft",
        "title": "Mathematical digit streams as LP2 keys",
        "question": "Do the specified base-29 mathematical streams decode LP2 under a drift-tolerant starting-position search?",
        "reader_question": "Could a mathematical constant or totient sequence be the key?",
        "summary": "Pinned public Stages AG and AH test 21 distinct number streams across LP2 sections with a drift-tolerant key start; none reaches the source's reading threshold.",
        "finding": "All 19,140 source settings scored below the +30 reading threshold. Every 729-rune-or-longer stream/alignment/mode group met the source exclusion rule; the 66 undecided groups contain only nine runes each. The complete source outputs were replayed byte-for-byte.",
        "limitations": "This tests only the pinned digit/arithmetic streams, GP29 representation, three arithmetic directions, 1,000 starting positions and source frequency model. The source's score is not adjusted over the whole grid. A nine-rune section cannot decide the remaining groups.",
        "next_steps": "A different number-key proposal needs a fixed digit rule, key alignment and predictive success criterion before examining LP2; use a planted control under the proposed rule.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "number streams", "base 29", "totient", "mathematical keys"],
        "scope": {
            "pages": [f"lp2-{n:02d}" for n in range(56)],
            "artifacts": [PREFIX + "plan.json", PREFIX + "source-stage_ag_candidates.tsv",
                          PREFIX + "source-stage_ah_candidates.tsv"],
            "representation": "Pinned source 12,956 GP29 runes in sections 7–15; Liberpedia LP2-00–55 pages independently reproduce the complete rune stream.",
            "procedure": "Replay Wulfic Stages AG and AH, validate all source candidate/control tables byte-for-byte, and independently check the parameter grid, page stream, arithmetic prefixes and duplicate stream.",
            "parameters": "10 AG names and 12 AH names (21 distinct streams); nine separate sections plus one continuous stream; sub/add/Beaufort; 29 shifts; 1,000 uniform start positions; score pass >=30, cell exclusion <=-10 for all shifts after controls pass.",
            "exclusions": "Other numeric representations, stream sources, key starts, boundary treatments, language priors, cipher directions and state equations; the short nine-rune section remains inconclusive."
        },
        "review": {
            "kind": "complete exact public-source replay with independent manuscript and grid checks",
            "retested_on": "2026-10-23",
            "reviewer": "Pinned source tables reproduced byte-for-byte; independent site rune-stream, parameter-grid, control and arithmetic-prefix checks",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python experiments/records/wulfic-number-key-streams/run.py --check && python experiments/records/wulfic-number-key-streams/check.py && python experiments/records/wulfic-number-key-streams/plot.py --check",
            "environment": "Python 3.12 for bundled checks. Optional complete upstream replay uses the pinned Wulfic repository with NumPy, mpmath and Numba dependencies.",
            "script": PREFIX + "run.py",
            "script_sha256": digest(PREFIX + "run.py")["sha256"],
            "inputs": inputs,
            "outputs": [digest(p) for p in output_paths]
        },
        "visuals": [{"path": PREFIX + "comparison.svg",
                     "caption": "No tested setting meets the reading threshold; all undecided source groups contain just nine runes."}],
        "sources": [
            {"label": "Wulfic Stage AG at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ag.py"},
            {"label": "Wulfic Stage AH at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_ah.py"},
            {"label": "Pinned published output tables", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"},
            {"label": "Master transcription provenance", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/data/canonical/PROVENANCE.md"}
        ],
        "related": ["wulfic-stage-ab-reset-alphabets", "wulfic-stage-af-unit-shifts", "sectionwise-rune-profile"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
