#!/usr/bin/env python3
"""Replay every B-05 Part 2a two-witness payload mask with pinned upstream code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "grid-payload-prf-seed-corner"
SOURCE = PILOT / "source/liber-primus"
SUMMARY = HERE / "results.json"
CASES = HERE / "cases.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate() -> tuple[dict, dict]:
    with tempfile.TemporaryDirectory(prefix="liberpedia-b05-masks-") as tmp:
        root = Path(tmp) / "liber-primus"
        shutil.copytree(SOURCE, root)
        lane = root / "analysis/round13/B05"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
        subprocess.run([sys.executable, str(lane / "control.py")],
                       capture_output=True, text=True, encoding="utf-8", env=env, check=True)
        control = json.loads((lane / "control_results.json").read_text(encoding="utf-8"))
        assert control["overall_pass"] and len(control["cases"]) == 4
        assert all(gate["PASS"] for gate in control["gates"])
        sys.path.insert(0, str(lane))
        import sweep  # type: ignore[import-not-found]
        import prf  # type: ignore[import-not-found]

        assert len(sweep.UNS) == 12956 and len(sweep.HEADSEQ) == 400
        assert len(prf.CONTESTED) == 6 and len(prf.GENERATORS) == 15
        nmean, nmax, _ = sweep.null_band(200)
        rows, _, _ = sweep.part2a(max(sweep.HIT_SCORE, nmax))
        assert len(rows) == 64 * 15 * 2 * 2 == 3840
        cases = [{
            "mask": row["mask"], "generator": row["gen"],
            "reduction": row["red"], "sign": row["sign"],
            "score": round(row["score"], 6),
        } for row in rows]
        best = cases[0]
        hits = [row for row in cases if row["score"] >= sweep.HIT_SCORE and row["score"] > nmax]
        output = {
            "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "source_part": "B-05 Part 2a",
            "case_count": len(cases),
            "target_runes": len(sweep.UNS),
            "screen_runes": len(sweep.HEADSEQ),
            "scope": "64 two-witness masks at six fixed byte positions × 15 PRFs × two byte reductions × two signs; offset zero, forward, no Atbash",
            "contested_positions": prf.CONTESTED,
            "null": {"method": "source's 200 shuffled 400-rune heads", "mean": round(nmean, 6), "max": round(nmax, 6)},
            "threshold": {"english_floor": sweep.HIT_SCORE, "null_max": round(nmax, 6),
                          "rule": "score >= -5.5 and score > null maximum"},
            "control": {"all_pass": control["overall_pass"],
                        "generators": [case["gen"] for case in control["cases"]],
                        "correct_scores": [round(case["beam_correct"], 6) for case in control["cases"]],
                        "character_recovery": [round(case["char_recovery"], 6) for case in control["cases"]]},
            "best": best,
            "hit_count": len(hits),
            "input_sha256": {
                "majority_payload": digest(SOURCE / "analysis/pp49_51/canon_256.bin"),
                "decimal_preferred_payload": digest(SOURCE / "analysis/pp49_51/canon_256_decpref.bin"),
                "rune_transcription": digest(SOURCE / "data/krisyotam_runes.txt"),
                "quadgram_model": digest(SOURCE / "data/english_quadgrams.txt"),
            },
        }
        attachment = {"schema": "liberpedia-b05-contested-mask-cases-v1",
                      "source_part": "B-05 Part 2a", "cases": cases}
        return output, attachment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare fresh replay with saved output")
    parser.add_argument("--write", action="store_true", help="regenerate saved output during development")
    args = parser.parse_args()
    summary, cases = calculate()
    if args.write:
        SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n")
        CASES.write_text(json.dumps(cases, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    if args.check:
        assert summary == json.loads(SUMMARY.read_text(encoding="utf-8"))
        assert cases == json.loads(CASES.read_text(encoding="utf-8"))
    print(f"source controls pass; {summary['case_count']} masks × generator cases; "
          f"best {summary['best']['score']:.3f}; hits {summary['hit_count']}")


if __name__ == "__main__":
    main()
