"""Write the Stage N draft record with exact local dependency hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = f"experiments/records/{HERE.name}/"


def hashed(name: str) -> dict[str, str]:
    return {"path": name, "sha256": hashlib.sha256((ROOT / name).read_bytes()).hexdigest()}


if __name__ == "__main__":
    artifacts = [BASE + "source-stage_n_results.tsv", BASE + "source-profile.json",
                 "exports/alphanumeric-grids.csv"]
    inputs = [BASE + name for name in ("plan.json", "check.py", "plot.py", "prepare_source.py",
                                       "replay_source.py", "make_plan.py", "make_record.py")]
    inputs += artifacts
    record = {
        "id": HERE.name, "status": "draft",
        "title": "Cicada-derived keys against the LP2 grid",
        "question": "Do Wulfic's fixed earlier-Cicada key streams make the 256-cell LP2 grid pass its byte or GP29 reading screens?",
        "reader_question": "Do known Cicada numbers unlock the 256-cell grid?",
        "summary": "Exact Stage N replay finds no source-screen hit among 456 settings: 72 byte-key operations and 384 GP29 readings. The screens have only post-replay synthetic detector diagnostics.",
        "finding": "The best byte output is 42.6% printable, below the source's 90% screen, with no named signature. The highest rune log likelihood is 4.63 nats, below +30. No source setting passes.",
        "limitations": "The source uses one row-order grid and reversal, specified key starts/streams, a permissive byte-printability or offset-zero signature screen, and a solved-LP1 unigram detector. Planted controls were added after replay and do not establish power against all plausible LP2 messages.",
        "next_steps": "For another grid-key hypothesis, specify the key bytes, start, operation, route and full-stream success criterion before testing; calibrate its detector on planted examples of the intended message type.",
        "outcome": "inconclusive",
        "tags": ["LP2", "grid", "source replay", "key stream", "byte decode", "rune decode"],
        "scope": {
            "pages": ["lp2-49", "lp2-50", "lp2-51"], "artifacts": artifacts,
            "representation": "Printed 32×8 grid as 256 base-60-derived bytes or 512 separate base-60 digits, conditionally using the site's pinned digit order; forward and full reverse only.",
            "procedure": "Replay source Stage N all 456 rows, independently rebuild the grid from site export, repeat 72 byte transforms and 384 GP29 likelihood calculations, then run explicitly post-replay synthetic detector diagnostics.",
            "parameters": "12 finite byte keys×3 operations×2 directions=72; two GP29 grid encodings×2 directions×3 decode modes×(29 constant shifts+3 rune streams)=384; source thresholds 90% printable or listed signature, and log LR+30 nats.",
            "exclusions": "Other grid layouts, ten disputed stems, later offsets, decryption-plus-decompression, other key derivations/starts, different scoring languages and plaintext interpretation beyond the source screens."
        },
        "review": {
            "kind": "exact public-source replay with post-replay detector diagnostics",
            "retested_on": "2026-10-23",
            "reviewer": "456-row source output reproduced byte-for-byte; site grid and all byte/rune scores independently recalculated from pinned numerical source inputs",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python " + BASE + "run.py --check && python " + BASE + "check.py && python " + BASE + "plot.py --check",
            "environment": "Python 3 standard library for bundled verification. Optional source replay/profile export requires the pinned Wulfic checkout with its dependencies.",
            "script": BASE + "run.py", "script_sha256": hashed(BASE + "run.py")["sha256"],
            "inputs": [hashed(name) for name in inputs],
            "outputs": [hashed(BASE + name) for name in ("results.json", "comparison.svg")]
        },
        "visuals": [{"path": BASE + "comparison.svg", "caption": "Best of the fixed source screens compared with their separate pass thresholds."}],
        "sources": [
            {"label": "Wulfic Stage N at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_n.py"},
            {"label": "Pinned source findings", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"}
        ],
        "related": ["grid-direct-bytes", "wulfic-native-key-streams"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
