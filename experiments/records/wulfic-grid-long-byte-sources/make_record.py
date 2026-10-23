"""Refresh Stage Y draft metadata and exact local byte hashes."""
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
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["cell_count"] == 96 and result["phase_trials"] == 2865136
    assert result["source_positive_controls"] == 24 and result["source_negative_controls"] == 18
    assert result["passing_cells"] == 0
    inputs = [BASE + x for x in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                  "make_record.py", "source-stage_y_results.tsv",
                                  "source-stage_y_controls.tsv")]
    inputs += [entry["path"] for entry in json.loads((HERE / "plan.json").read_text(encoding="utf-8"))["bundled_source_bytes"]]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Archived byte streams against the LP2 number grid",
        "question": "Can any cyclic phase of six archived byte streams turn the LP2 number grid into a low-diversity byte block under four routes and four byte operations?",
        "reader_question": "Do archived byte streams reveal a low-diversity grid message?",
        "summary": "Exact Wulfic Stage Y replay finds no source/route/operation cell meeting its distinct-byte threshold after all cyclic phases; full controls pass.",
        "finding": "All 24 source planted positives pass and all 18 negative controls stay above the cutoff. None of 96 source/route/operation cells has a phase with D≤120 distinct bytes; the minimum is D=139 over 2,865,136 phase trials. Both pinned source tables were reproduced byte-for-byte, and an independent checker recomputed every LP2 phase from the site grid and bundled byte inputs.",
        "limitations": "This excludes low-diversity output under these six exact source bytes, four routes, four operations and all cyclic phases. It does not exclude a high-diversity plaintext, another key, different grid construction, altered key schedule, other decoding layer or another language.",
        "next_steps": "A related proposal should specify a new source byte stream or transformation and predict a complete output, not select favorable fragments after inspecting many phases.",
        "outcome": "not-supported",
        "tags": ["LP2", "number grid", "source replay", "running key", "byte operation", "control gate"],
        "scope": {
            "pages": ["lp2-49", "lp2-50", "lp2-51"],
            "artifacts": [BASE + "source-stage_y_results.tsv", BASE + "source-stage_y_controls.tsv"],
            "representation": "The 256 printed 32×8 grid cells parsed as base-60 byte values from Liberpedia's exact token export.",
            "procedure": "For each of six pinned source byte streams, all cyclic phases, row/row-reverse/column/column-reverse and XOR/grid-minus-key/grid-plus-key/key-minus-grid, count distinct values in the complete 256-byte output. Preserve source positive and negative gates and independently recompute all LP2 minima.",
            "parameters": "Six source streams; 16 route/operation cells each; 2,865,136 source-phase trials. D≤120 passes. Twenty-four source positives at their planted cells, 18 uniform-grid negatives, and negative mean D within 162.0±0.5 are required for a valid run.",
            "exclusions": "Other sources, partial or reordered bytes, offsets in grid or file structures beyond the source's cyclic key phase, alternate statistics and later decoding layers."
        },
        "review": {
            "kind": "exact public-source Stage Y replay with independent exhaustive phase audit",
            "retested_on": "2026-10-23",
            "reviewer": "Pinned source 97-row results and 43-row controls TSVs reproduced byte-for-byte; independent checker recomputes all 2,865,136 LP2 phases and exact published cell metrics",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}run.py --check && python {BASE}plot.py --check",
            "environment": "Python 3 and NumPy for the bundled full-phase checker. Optional pinned-source replay also uses NumPy and an external Wulfic checkout.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(x) for x in inputs],
            "outputs": [hashed(BASE + x) for x in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Lowest complete-block distinct-byte count across all phases and 16 route/operation cells for each source. The declared pass level is 120."}],
        "sources": [
            {"label": "Pinned Wulfic Stage Y source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_y.py"},
            {"label": "Pinned Stage Y result table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_y_results.tsv"},
            {"label": "Pinned Stage Y control table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_y_controls.tsv"}
        ],
        "related": ["wulfic-grid-native-keys", "wulfic-grid-periodic-byte-invariant", "grid-direct-bytes"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
