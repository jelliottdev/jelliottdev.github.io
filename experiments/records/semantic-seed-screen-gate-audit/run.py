#!/usr/bin/env python3
"""Audit the pinned R26-C screen; --replay reruns the 4,274 source cases.

The bundled upstream source is MIT-licensed and pinned to commit
f08b20b632d91209ddbaa747e8e2f23df0c78ba1. The unavailable language-panel
model is deliberately not reconstructed or replaced. No cipher failure is inferred.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "liber-primus"
ROWS = HERE / "rows.jsonl"
RESULTS = HERE / "results.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen_bar_from_source() -> float:
    module = ast.parse((SOURCE / "analysis/round26/C/sweep.py").read_text())
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "SCREEN_BAR"
            for target in statement.targets
        ):
            return float(ast.literal_eval(statement.value))
    raise AssertionError("upstream SCREEN_BAR is missing")


def planted_screen() -> dict:
    lane = SOURCE / "analysis/round26/C"
    sys.path.insert(0, str(lane))
    import control  # type: ignore[import-not-found]
    import driftbeam  # type: ignore[import-not-found]

    plain = control.english_plain(240)
    key = control.ZOO["py27_random29"](3301)
    cipher = control.enc_skip_by_two(plain, key)
    decoded = driftbeam.beam_decode(
        cipher[:120], key, sign=-1, o=0, beam_w=64,
        **driftbeam.PRESETS["pair"]
    )
    return {
        "generator": "py27_random29",
        "seed": 3301,
        "decoder": "pair",
        "runes": 120,
        "recovered": sum(a == b for a, b in zip(decoded["plain_idx"], plain[:120])),
        "screen_score": round(decoded["score"], 4),
        "escalated": decoded["score"] >= screen_bar_from_source(),
    }


def check() -> dict:
    source_seeds = json.loads((SOURCE / "analysis/round26/C/seeds.json").read_text())
    sys.path.insert(0, str(SOURCE / "analysis/round26/C"))
    import build_seeds  # type: ignore[import-not-found]
    assert build_seeds.build() == source_seeds["seeds"], "seed builder drifted"
    assert (source_seeds["n_total"], source_seeds["n_int"], source_seeds["n_str"]) == (323, 292, 31)

    rows = [json.loads(line) for line in ROWS.open(encoding="utf-8")]
    assert len(rows) == 4274
    bar = screen_bar_from_source()
    assert bar == 5.0
    scores = [float(row["screen_score"]) for row in rows]
    assert max(scores) < bar
    # score.py builds every quadgram score as log10(count / total) and its
    # unseen floor as log10(0.01 / total); every term is non-positive.
    from lp import score  # type: ignore[import-not-found]
    q = score.Quadgram()
    assert max(q.d.values()) <= 0 and q.floor <= 0
    plant = planted_screen()
    assert plant["recovered"] == 120 and not plant["escalated"]

    result = {
        "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
        "seed_count": 323,
        "integer_seeds": 292,
        "string_seeds": 31,
        "case_count": len(rows),
        "generator_count": 7,
        "decoder_count": 2,
        "screen_bar": bar,
        "screen_score_min": min(scores),
        "screen_score_median": statistics.median(scores),
        "screen_score_max": max(scores),
        "screen_escalations": sum(s >= bar for s in scores),
        "iocN_median": statistics.median(row["iocN"] for row in rows),
        "entropy_median": statistics.median(row["entropy"] for row in rows),
        "source_rows_sha256": sha(ROWS),
        "source_seeds_sha256": sha(SOURCE / "analysis/round26/C/seeds.json"),
        "planted_screen": plant,
        "full_panel_gate_replayed": False,
        "finding": "The +5 screen bar cannot be reached by a normalized log10 quadgram probability, so the full gate never runs.",
    }
    if RESULTS.exists():
        expected = json.loads(RESULTS.read_text(encoding="utf-8"))
        assert result == expected, "saved result differs from current source or rows"
    return result


def replay() -> None:
    """Run unmodified upstream sweep in a disposable copy and compare every row."""
    with tempfile.TemporaryDirectory(prefix="liberpedia-r26-") as tmp:
        copy = Path(tmp) / "liber-primus"
        shutil.copytree(SOURCE, copy)
        lane = copy / "analysis/round26/C"
        import os
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        subprocess.run([sys.executable, str(lane / "build_seeds.py")], check=True, env=env)
        assert json.loads((lane / "seeds.json").read_text())["seeds"] == json.loads(
            (SOURCE / "analysis/round26/C/seeds.json").read_text()
        )["seeds"]
        subprocess.run([sys.executable, str(copy / "analysis/round19/G3/gen_py27.py"), "--selftest"], check=True, env=env)
        subprocess.run([sys.executable, str(lane / "sweep.py")], check=True, env=env)
        replay_rows = [json.loads(line) for line in (lane / "rows.jsonl").open(encoding="utf-8")]
        saved_rows = [json.loads(line) for line in ROWS.open(encoding="utf-8")]
        assert replay_rows == saved_rows, "source sweep rows differ"
        print(f"replayed {len(replay_rows):,} source screen rows; all match")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify saved source audit quickly")
    parser.add_argument("--replay", action="store_true", help="rerun all 4,274 source screen rows (~3 minutes)")
    args = parser.parse_args()
    result = check()
    print(f"verified {result['case_count']:,} rows; plant {result['planted_screen']['recovered']}/120 discarded by +5 screen")
    if args.replay:
        replay()


if __name__ == "__main__":
    main()
