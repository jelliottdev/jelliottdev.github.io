"""Independent accounting and source-result checks for the pinned F-01 replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LP = HERE / "source/liber-primus"
OUT = LP / "analysis/round16/F-01/results.json"
ORIGINAL = LP / "analysis/round16/F-01/original_results.json"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
TARGETS = {"T1_cicada_2012_2013", "T2_lp1_solved", "T3_pgp_messages",
           "T4_anend_hash", "T6_lp2_head_200"}
KEYS = {"lp2_fwd", "lp2_rev", "lp2_atbash", "lp2_neg"}


def substantive(data: dict) -> dict:
    """Runtime varies, while all model outputs and scores must agree exactly."""
    return {key: value for key, value in data.items() if key != "elapsed_s"}


def verify(result_path: Path = OUT) -> dict:
    got = json.loads(result_path.read_text(encoding="utf-8"))
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    assert substantive(got) == substantive(original), "Replay differs from pinned source output"

    corpus = (LP / "data/krisyotam_runes.txt").read_text(encoding="utf-8")
    sections = corpus.split("%")
    indices = {rune: i for i, rune in enumerate(RUNES)}
    unsolved = [indices[rune] for section in sections[:55] for rune in section if rune in indices]
    assert len(unsolved) == 12956
    assert hashlib.sha256(",".join(map(str, unsolved)).encode()).hexdigest() == (
        "023312066df471005264b9cbe7997cb77d2a9a6a2dc9b3316d22674023af1585"
    )

    rows = got["results"]
    assert got["positive_control_passed"] is True
    control = got["positive_control"]
    assert control["gate"] == "PASS" and control["char_recovery"] == 1
    assert control["beam_score"] > control["rigid_score"] + .5
    assert control["beam_score"] > control["null_max"] + .5
    assert got["n_decodes"] == len(rows) == len(TARGETS) * len(KEYS) * 2 == 40
    assert {(r["target"], r["key_variant"], r["sign"]) for r in rows} == {
        (target, key, sign) for target in TARGETS for key in KEYS for sign in (-1, 1)
    }
    assert all(r["target_len"] in (63, 200, 500) for r in rows)
    assert all(r["score"] < got["bar"] for r in rows)
    assert got["best_score"] == max(r["score"] for r in rows)
    assert got["best_row"]["score"] == got["best_score"]
    assert got["bar"] == -5.5 and got["any_hit"] is False
    # Null comparisons exist only for the highest-ranked five configurations.
    assert sum("null_max" in r for r in rows) == 5
    assert all(r["score"] < r["null_max"] for r in rows if "null_max" in r)
    return {"key_runes": len(unsolved), "targets": len(TARGETS), "decodes": len(rows),
            "best_score": got["best_score"], "advancement_bar": got["bar"],
            "null_tested": 5, "source_output_match": True}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
