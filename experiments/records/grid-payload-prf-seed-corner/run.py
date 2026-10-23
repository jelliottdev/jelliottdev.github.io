#!/usr/bin/env python3
"""Replay a fixed 32-case corner of Dukotah's pinned B-05 payload-as-PRF test.

This uses the upstream generators, beam, 400-rune ciphertext head, 200 shuffles,
and planted controls. It deliberately does not imply coverage of the full B-05
grid or any other payload/key construction.
"""
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
SOURCE = HERE / "source/liber-primus"
RESULTS = HERE / "results.json"
GENERATORS = ("sha256_ctr", "rc4", "hmac_drbg_sha256", "aes256_ctr_k")
REDUCTIONS = ("mod", "reject")
SIGNS = (-1, 1)
REPS = ("maj.raw", "dec.raw")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate() -> dict:
    # The upstream control writes into its own directory; a disposable copy
    # keeps the checked-in source untouched and leaves no generated files.
    with tempfile.TemporaryDirectory(prefix="liberpedia-b05-") as tmp:
        root = Path(tmp) / "liber-primus"
        shutil.copytree(SOURCE, root)
        lane = root / "analysis/round13/B05"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}
        proc = subprocess.run(
            [sys.executable, str(lane / "control.py")],
            capture_output=True, text=True, encoding="utf-8", env=env, check=True,
        )
        control = json.loads((lane / "control_results.json").read_text(encoding="utf-8"))
        assert control["overall_pass"] and len(control["cases"]) == 4, proc.stdout
        assert all(item["PASS"] for item in control["gates"])

        sys.path.insert(0, str(lane))
        import prf  # type: ignore[import-not-found]
        import sweep  # type: ignore[import-not-found]

        assert len(sweep.HEADSEQ) == 400 and len(sweep.UNS) == 12956
        payloads = prf.load_payloads()
        assert all(len(p) == 256 for p in payloads)
        nmean, nmax, _ = sweep.null_band(200)
        rows = []
        for rep, seed in zip(REPS, payloads):
            for generator in GENERATORS:
                for reduction in REDUCTIONS:
                    key = prf.keystream(seed, generator, reduction, 400 * 4 + 64)
                    for sign in SIGNS:
                        decoded = sweep.sk.beam_decode(
                            sweep.HEADSEQ, key, sign=sign, o=0,
                            beam_w=120, max_skip=3,
                        )
                        rows.append({
                            "representation": rep,
                            "generator": generator,
                            "reduction": reduction,
                            "sign": sign,
                            "score": round(decoded["score"], 6),
                        })
        assert len(rows) == 32
        bar = -5.5
        best = max(rows, key=lambda row: row["score"])
        result = {
            "source_commit": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "case_count": len(rows),
            "target_runes": len(sweep.UNS),
            "screen_runes": len(sweep.HEADSEQ),
            "scope": "two canonical raw 256-byte payloads × four named PRFs × two reductions × two signs; forward key, no Atbash, offset zero",
            "null": {"method": "source's 200 shuffled 400-rune heads", "mean": round(nmean, 6), "max": round(nmax, 6)},
            "threshold": {"english_floor": bar, "null_max": round(nmax, 6), "rule": "score >= -5.5 and score > null maximum"},
            "control": {
                "all_pass": control["overall_pass"],
                "cases": [{
                    "generator": case["gen"],
                    "reduction": case["red"],
                    "correct_score": round(case["beam_correct"], 6),
                    "wrong_score": round(case["beam_wrong"], 6),
                    "one_byte_flip_score": round(case["beam_one_contested_byte_flipped"], 6),
                    "character_recovery": round(case["char_recovery"], 6),
                } for case in control["cases"]],
            },
            "best": best,
            "hits": [row for row in rows if row["score"] >= bar and row["score"] > nmax],
            "rows": rows,
            "input_sha256": {
                "majority_payload": digest(SOURCE / "analysis/pp49_51/canon_256.bin"),
                "decimal_preferred_payload": digest(SOURCE / "analysis/pp49_51/canon_256_decpref.bin"),
                "rune_transcription": digest(SOURCE / "data/krisyotam_runes.txt"),
                "quadgram_model": digest(SOURCE / "data/english_quadgrams.txt"),
            },
        }
        return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare fresh computation with saved results")
    parser.add_argument("--write", action="store_true", help="regenerate saved results during development")
    args = parser.parse_args()
    result = calculate()
    if args.write:
        RESULTS.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.check:
        assert result == json.loads(RESULTS.read_text(encoding="utf-8")), "result drifted"
    print(f"controls pass; {result['case_count']} cases; best {result['best']['score']:.3f}; hits {len(result['hits'])}")


if __name__ == "__main__":
    main()
