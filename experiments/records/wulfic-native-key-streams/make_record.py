"""Refresh the draft record and its exact content hashes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PREFIX = "experiments/records/wulfic-native-key-streams/"


def digest(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


if __name__ == "__main__":
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    inputs = [digest(PREFIX + "plan.json")]
    inputs += [digest(PREFIX + name) for name in
               ("check.py", "plot.py", "replay_source.py", "calibrate.py", "make_plan.py", "make_record.py")]
    inputs += [digest(entry["path"]) for entry in plan["inputs"]]
    record = {
        "id": "wulfic-native-key-streams", "status": "draft",
        "title": "Prime, solved-text and grid streams as LP2 keys",
        "question": "Do six source-defined streams of primes, solved LP1 values and number-grid values yield LP2 readings under a drift-tolerant GP29 decoder?",
        "reader_question": "What happens when Cicada's own numbers are used as a key?",
        "summary": "A pinned public replay finds no reading in 5,742 source settings. Planted controls show the detector can recognize the specified finite keys over a usable prefix.",
        "finding": "Zero Stage I/M settings pass the +30 reading threshold. Both source tables reproduce byte-for-byte. Supplemental post-replay diagnostics pass all 120 planted-key and reject all 120 wrong-key trials at preselected lengths within the keys; long Stage M alignments mostly test only a short key-bearing prefix.",
        "limitations": "The source starts each key at zero and scores only until a finite key ends. The supplemental controls were designed after the LP2 source results, not preregistered. Results do not cover cyclic keys, other starts, alternate grid transcriptions, other languages or other ciphers.",
        "next_steps": "State a precise alternative key alignment or extension rule before running a larger search; plant a full-length control under that rule and adjust for selecting many variants.",
        "outcome": "not-supported",
        "tags": ["LP2", "source replay", "prime key", "known readings", "number grid", "power check"],
        "scope": {
            "pages": [f"lp2-{i:02d}" for i in range(56)],
            "artifacts": [PREFIX + "plan.json", PREFIX + "source-stage_i_candidates.tsv",
                          PREFIX + "source-stage_m_candidates.tsv", "exports/alphanumeric-grids.csv"],
            "representation": "Pinned 12,956-rune section 7–15 stream plus three grid-relative windows; Stage I key values from source-solved LP1 text or primes, Stage M grid representations matching Liberpedia's 256 tokens.",
            "procedure": "Replay pinned Stage I and M complete candidate grids, then measure a separately identified post-replay planted-key diagnostic within each finite key's usable length.",
            "parameters": "Three Stage I keys × 10 alignments and three Stage M keys × 12 alignments; all three sub/add/Beaufort directions and 29 shifts; start at zero; source reading threshold log LR >=30. Supplemental 20 planted and 20 wrong-key draws per stream.",
            "exclusions": "Other start positions or cycling, arbitrary LP1-derived streams, different grid bytes or digit mappings, different scoring language, and Stage I's separate nine-rune vocabulary check."
        },
        "review": {
            "kind": "exact public-source replay with bounded post-replay power diagnostic",
            "retested_on": "2026-10-23",
            "reviewer": "Two complete source TSVs reproduced byte-for-byte; independent site rune/grid and parameter-grid checks; planted/wrong-key detector controls",
            "human_review": "pending"
        },
        "reproduction": {
            "command": "python experiments/records/wulfic-native-key-streams/run.py --check && python experiments/records/wulfic-native-key-streams/check.py && python experiments/records/wulfic-native-key-streams/plot.py --check",
            "environment": "Python 3.12 for bundled checks. Optional full source replay and controls require a pinned Wulfic checkout with its NumPy dependencies.",
            "script": PREFIX + "run.py",
            "script_sha256": digest(PREFIX + "run.py")["sha256"],
            "inputs": inputs,
            "outputs": [digest(PREFIX + "results.json"), digest(PREFIX + "comparison.svg")]
        },
        "visuals": [{"path": PREFIX + "comparison.svg",
                     "caption": "LP2's best score for each source key remains below the reading threshold; the bounded planted controls score above it."}],
        "sources": [
            {"label": "Wulfic Stage I source at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_i.py"},
            {"label": "Wulfic Stage M source at pinned revision", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/blob/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/tools/run_stage_m.py"},
            {"label": "Pinned source output tables", "url": "https://github.com/Wulfic/Cicada3301-Liber_Primus/tree/bf89d3d13aad2b8f2c95ab195cf1b092f250775c/reference/findings"}
        ],
        "related": ["wulfic-number-key-streams", "grid-direct-bytes", "solved-reading-running-key"]
    }
    (HERE / "record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
