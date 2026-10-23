"""Refresh Stage R draft metadata from checked record files."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def main():
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert result["candidate_count"] == 43500 and result["control_count"] == 200
    assert result["candidate_pass_count"] == 0 and result["candidate_max_rounded"] == 2.41
    assert result["title_runes"] == 9 and result["title_settings"] == 4350
    assert result["title_absolute_score_bound"] < 30 and result["best_non_title_rounded"] == -50.75
    assert result["candidate_exact_tsv_sha256"] == "7636b6e93acc24f221ce5e7ef70419a17ff238c3a0d94becb69ece22707d1949"
    assert result["control_exact_tsv_sha256"] == "e302f6009e63ba17de950ad396be2001a2c922d047e0da83b22990efefb6a29b"
    inputs = [BASE + x for x in (
        "plan.json", "fast.py", "replay.py", "bundle.py", "parity.py", "plot.py", "make_record.py",
        "source-profile.npz", "source-stage_r_candidates.tsv", "source-stage_r_controls.tsv"
    )]
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Archived Cicada numbers and byte streams as LP2 keys",
        "question": "Do 25 archived number or byte sources recover LP2 under the pinned phase-averaged stay/advance/skip key detector?",
        "reader_question": "Do Cicada number and byte streams work as LP2 keys?",
        "summary": "Exact accelerated replay of the pinned Stage R source grid finds no candidate above its declared +30 line; all planted controls pass.",
        "finding": "All 43,500 LP2 candidate rows and 200 control rows match the pinned source tables at published 0.01-nat precision. No LP2 setting reaches +30. The highest score, +2.41, is on the nine-rune title; its absolute score ceiling is only +11.19, so its 4,350 settings could never pass. The best other section scores −50.75, and the complete joined text peaks at −1,479.67. Correct-key planted controls score at least +169.09 and wrong-key controls at most −60.86. The compiled scorer agrees with the source on real and synthetic parity cases.",
        "limitations": "The nine-rune title is too short for this +30 threshold under any key, so those 4,350 settings are not informative negatives. This screen uses only the source's 25 inputs, two GP29 mappings, ten transcript alignments, three arithmetic modes, 29 shifts, solved-LP1 unigram model, drift probabilities and uniform start-phase prior. Controls show power for this generated model at two longer lengths, not for every LP2 construction. Other preprocessing, keys, schedules, language models and cipher layers remain untested.",
        "next_steps": "Specify a materially different source transformation or key schedule before treating another candidate as an untested case; validate a full output with a planted control and fixed score rule.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "running key", "cyclic phase", "Cicada sources", "drift model"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [BASE + "source-stage_r_candidates.tsv", BASE + "source-stage_r_controls.tsv"],
            "representation": "Source GP29 rune transcript in sections 7–15 and their continuous join, covering unsolved LP2-00–55; section labels are not manuscript page numbers.",
            "procedure": "Read 25 pinned number/byte sources into modulo-29 and rejection-mapped key streams. For each of 50 keys and ten section alignments, score three arithmetic modes and all 29 shifts with the pinned phase-averaged stay/advance/skip HMM. Replay 200 planted positive/negative pairs with exact seed. Compare all serialized rows against the pinned Stage R tables.",
            "parameters": "50 mapped streams × 10 alignments × 3 modes × 29 shifts = 43,500 source settings; +30-nat pass line; uniform cyclic phase, transition 0.02/0.96/0.02, epsilon 0.1, pruning 1e−12. Control lengths 729 and 3316, fresh/next rekey, keep 0.19, RNG seed 3301.",
            "exclusions": "Other source bytes, ordering, mapping, page segmentation, selected rather than averaged phase, alternative drift/rekey model, key operations, plaintext prior or downstream layer."
        },
        "review": {
            "kind": "exact public-source Stage R grid replay with accelerated independent forward sum",
            "retested_on": "2026-10-23",
            "reviewer": "All 43,500 candidate and 200 control rows reproduced at original 0.01-nat precision; original-scorer parity on real and synthetic cases; numeric input bundle and checker supplied",
            "human_review": "pending"
        },
        "reproduction": {
            "command": f"python {BASE}check.py && python {BASE}plot.py --check",
            "environment": "Python 3 with NumPy and Numba for the packaged numeric checker. Full pinned-source reconstruction also requires the external Wulfic checkout at the stated commit.",
            "script": BASE + "check.py", "script_sha256": hashed(BASE + "check.py")["sha256"],
            "inputs": [hashed(path) for path in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Extremal source positive control, LP2 candidate and wrong-key control scores against +30. The highest LP2 score comes from a nine-rune section that can never reach the pass line. Each point is a group extremum."}],
        "sources": [
            {"label": "Pinned Wulfic Stage R source", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_r.py"},
            {"label": "Pinned Stage R candidate table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_r_candidates.tsv"},
            {"label": "Pinned Stage R control table", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings/stage_r_controls.tsv"}
        ],
        "related": ["wulfic-number-key-streams", "wulfic-native-key-streams", "wulfic-keyword-quagmire-models"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
