#!/usr/bin/env python3
"""Replay the B-05 rigid channel and exact top-five full-page follow-ups."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
LANE = HERE.parent / "grid-payload-prf-seed-corner/source/liber-primus/analysis/round13/B05"
sys.path.insert(0, str(LANE))
import prf  # type: ignore[import-not-found]  # noqa: E402
import sweep  # type: ignore[import-not-found]  # noqa: E402

OUTPUT = HERE / "followup.json"


def source_head(row: dict) -> float:
    seed = prf.representations()[row["rep"]]
    key = prf.keystream(seed, row["gen"], row["red"], sweep.TOTAL_KS)
    if row["direction"] == "rev":
        key = key[::-1]
    if row["atbash"]:
        key = prf.atbash(key)
    return sweep.sk.beam_decode(sweep.HEADSEQ, key, sign=row["sign"],
                                o=row["offset"], beam_w=sweep.BEAM_W,
                                max_skip=sweep.MAX_SKIP)["score"]


def calculate(max_full: int = 5, resume: bool = False) -> dict:
    rows = [json.loads(line) for line in (HERE / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    main = [r for r in rows if r["part"] == "part1"]
    assert len(main) == 40320
    # Recompute 100 strongest HEAD scores at full precision before selecting
    # five. Rounded six-decimal output could otherwise alter a close rank.
    head100 = sorted(main, key=lambda r: r["score"], reverse=True)[:100]
    ranked = sorted(enumerate(head100), key=lambda pair: source_head(pair[1]), reverse=True)
    best = [row for _, row in ranked[:5]]
    rigid = sweep.rigid_channel()
    full = []
    if resume and OUTPUT.exists():
        old = json.loads(OUTPUT.read_text(encoding="utf-8"))
        full = old.get("full_page", [])
        assert len(full) <= max_full
        assert [item["configuration"] for item in full] == best[:len(full)]
    for row in best[len(full):max_full]:
        exact = source_head(row)
        source_record = {"rep": row["rep"], "gen": row["gen"], "red": row["red"],
                         "dir": row["direction"], "atbash": row["atbash"],
                         "sign": row["sign"], "o": row["offset"], "score": exact}
        outcome = sweep.full_page(source_record)
        full.append({"configuration": row, "exact_head_score": round(exact, 6),
                     "full_score": round(outcome["full_score"], 6),
                     "full_text_head": outcome["head"]})
        print(f"full page {len(full)}/{max_full}: {outcome['full_score']:.3f}", flush=True)
        if resume:
            OUTPUT.write_text(json.dumps({"full_page": full}, indent=2) + "\n", encoding="utf-8")
    return {"source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "rigid_case_count": len(rigid),
            "rigid_best": {"rep": rigid[0]["rep"], "generator": rigid[0]["gen"],
                           "score": round(rigid[0]["score"], 6)},
            "rigid_rows": [{"rep": r["rep"], "generator": r["gen"],
                            "score": round(r["score"], 6)} for r in rigid],
            "full_page_total": 5,
            "full_page_completed": len(full),
            "full_page": full}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-full", type=int, choices=range(1, 6), default=5,
                        help="internal timing probe; publish only after all five")
    args = parser.parse_args()
    result = calculate(args.max_full, resume=args.write)
    if args.write:
        OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding="utf-8"))
    print(f"{result['rigid_case_count']} rigid corners; "
          f"{result['full_page_completed']} full-page follow-ups", flush=True)


if __name__ == "__main__":
    main()
