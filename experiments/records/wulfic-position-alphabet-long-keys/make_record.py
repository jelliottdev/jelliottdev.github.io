"""Refresh Stage W draft metadata and all local dependency hashes."""
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
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    counts = result["verdict_counts"]
    if result["void"]:
        summary = "Stage W's declared negative-control gate failed; its LP2 scores are reported but no exclusions are valid."
        finding = "At least one flat negative or shuffled-key null reaches the source threshold. The source declares this run VOID, so the candidate scores cannot support an exclusion."
    else:
        summary = ("Exact Stage W replay finds no hit among 50 long-byte-key/section settings; "
                   f"{counts['EXCLUDED']} are excluded by powered controls and "
                   f"{counts['untestable']} remain untestable under the source rule.")
        finding = ("The source's negative-control gate passes. No LP2 setting reaches its +30-nat threshold; "
                   f"all five positive controls detect {counts['EXCLUDED']} settings, while "
                   f"{counts['untestable']} lack that power. The best LP2 score is "
                   f"{result['best_lp2']['score']:.2f} nats, below threshold.")
    artifacts = [BASE + name for name in ("source-stage_s_dependency.tsv", "source-stage_w_controls.tsv",
                                          "source-stage_w_candidates.tsv")]
    inputs = [BASE + name for name in ("plan.json", "check.py", "plot.py", "replay_source.py",
                                      "make_record.py", "source-stage_s_dependency.tsv",
                                      "source-stage_w_controls.tsv", "source-stage_w_candidates.tsv")]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Long byte keys as position alphabets on LP2",
        "question": "Do five specified source byte streams serve as synchronized substitution-alphabet labels for LP2?",
        "reader_question": "Could these byte streams select the alphabet at each rune?",
        "summary": summary, "finding": finding,
        "limitations": "The model requires the named byte key to remain in step with each tested rune stream, with a fixed one-to-one substitution for every byte value. Short settings without detected positive controls are untestable; key skips, other phase rules and layered transformations remain open.",
        "next_steps": "Any different key or resynchronization rule needs its own declared alignment and same-length positive and flat-negative controls before drawing a negative conclusion.",
        "outcome": "inconclusive",
        "tags": ["LP2", "source replay", "byte key", "position alphabet", "control power"],
        "scope": {
            "pages": [f"lp2-{n:02d}" for n in range(56)], "artifacts": artifacts,
            "representation": "Canonical GP29 rune streams for each unsolved marked section 7–15 and the joined LP2-00–55 stream; five byte keys from the source hint file, its reversal and three source byte files. The three files' puzzle-payload provenance was not independently verified.",
            "procedure": "Replay the pinned Stage S LP2 dependency for these same 50 cells, then run unchanged Stage W source with its aligned controls; independently verify all control counts, phase bounds, source-score agreement and verdict rules.",
            "parameters": "Five key classings × ten section alignments; all source key phases; five same-length positives and five flat negatives per cell, plus one shuffled-key LP2 null per key; anti-doublet keep 0.19; source score threshold +30 nats.",
            "exclusions": "Other source Stage S classings, alternate byte encodings, offsets beyond source phases, key skips/restarts, changing alphabets, other plaintext distributions and composed ciphers."
        },
        "review": {
            "kind": "exact public-source Stage W replay with independent control/verdict check",
            "retested_on": "2026-10-23",
            "reviewer": "Both Stage W tables reproduced byte-for-byte against pinned published source; all 50 Stage S dependency rows agree with pinned full table; 505 controls and 50 decisions independently checked",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python " + BASE + "run.py --check && python " + BASE + "plot.py --check",
            "environment": "Bundled checks use Python 3 standard library. Optional full pinned-source replay requires NumPy and an external source checkout.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(path) for path in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg",
                     "caption": "Powered exclusions out of ten alignments per byte key. File 17/21/43 are source file names, not LP2 page numbers; unresolved settings lacked positive-control power."}],
        "sources": [
            {"label": "Wulfic Stage W at pinned revision",
             "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_w.py"},
            {"label": "Pinned Stage S score dependency",
             "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_s.py"},
            {"label": "Pinned published Stage W results",
             "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"}
        ],
        "related": ["wulfic-native-key-streams", "wulfic-number-key-streams"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
