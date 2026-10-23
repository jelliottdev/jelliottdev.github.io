#!/usr/bin/env python3
"""Extend the pinned B-05 planted control to all 15 PRFs and both reductions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE_LANE = HERE.parent / "grid-payload-prf-seed-corner/source/liber-primus/analysis/round13/B05"
sys.path.insert(0, str(SOURCE_LANE))
import control as upstream_control  # type: ignore[import-not-found]  # noqa: E402
import prf  # type: ignore[import-not-found]  # noqa: E402

OUTPUT = HERE / "control-all.json"


def calculate() -> dict:
    _, null_max, _ = upstream_control.nc.null_band(
        lambda s: upstream_control.nc.eng_norm(s), upstream_control.P, n=200, seed0=3301)
    cases = []
    for generator in prf.GENERATORS:
        for reduction in ("mod", "reject"):
            c = upstream_control.run_case(generator, reduction)
            gates = {
                "correct_above_english_and_null": c["beam_correct"] >= -5.5
                    and c["beam_correct"] >= null_max + 0.5,
                "beam_beats_rigid": c["beam_correct"] - c["rigid_correct"] > 1,
                "correct_beats_wrong": c["beam_correct"] - c["beam_wrong"] > 1,
                "recovery_above_80_percent": c["char_recovery"] > 0.8,
            }
            flip_sensitive = c["beam_correct"] - c["beam_one_contested_byte_flipped"] > 1
            cases.append({
                "generator": generator,
                "reduction": reduction,
                "correct_score": round(c["beam_correct"], 6),
                "wrong_score": round(c["beam_wrong"], 6),
                "one_byte_flip_score": round(c["beam_one_contested_byte_flipped"], 6),
                "rigid_correct_score": round(c["rigid_correct"], 6),
                "character_recovery": round(c["char_recovery"], 6),
                "one_byte_flip_sensitive": flip_sensitive,
                "gates": gates,
                "pass": all(gates.values()),
            })
    return {"source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "null_max": round(null_max, 6), "case_count": len(cases),
            "all_pass": all(case["pass"] for case in cases),
            "one_byte_flip_sensitive_count": sum(case["one_byte_flip_sensitive"] for case in cases),
            "cases": cases}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = calculate()
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding="utf-8"))
    print(f"{sum(c['pass'] for c in result['cases'])}/{result['case_count']} planted recovery controls pass; "
          f"{result['one_byte_flip_sensitive_count']} sensitive to byte 25")
    if not result["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
