"""Replay the source's 26 wrong-key extreme-value fits from its saved score rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source" / "liber-primus" / "analysis" / "round19" / "I1"
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
REPLAY = HERE / "replayed-tail.json"


def verify_inputs() -> None:
    for rel, expected in PLAN["source_inputs_sha256"].items():
        path = HERE / "source" / "liber-primus" / rel
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != expected:
            raise ValueError(f"Source input hash mismatch: {rel}")


def compare(saved: dict, actual: dict) -> None:
    assert saved.keys() == actual.keys()
    assert len(saved["fits"]) == len(actual["fits"]) == 26
    for left, right in zip(saved["fits"], actual["fits"]):
        assert left.keys() == right.keys()
        for key in left:
            a, b = left[key], right[key]
            if isinstance(a, float):
                assert math.isclose(a, b, rel_tol=0, abs_tol=1e-10), (left["null"], left["mode"], key)
            else:
                assert a == b, (left["null"], left["mode"], key)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="compare saved replay to source without recomputing")
    ap.add_argument("--capture", action="store_true", help="write first replay receipt after source execution")
    args = ap.parse_args()
    verify_inputs()
    archived = json.loads((SOURCE / "out_fp_tail.json").read_text(encoding="utf-8"))
    if args.check:
        compare(archived, json.loads(REPLAY.read_text(encoding="utf-8")))
        print("PASS: saved 26 fits match archived source fields")
        return
    with tempfile.TemporaryDirectory(prefix="liberpedia-i1-tail-") as temp:
        staged = Path(temp)
        for name in ("analyse_fp.py", "out_fp_deep.json", "out_fp_deep2.json", "out_fp_curve.json"):
            shutil.copyfile(SOURCE / name, staged / name)
        subprocess.run([sys.executable, str(staged / "analyse_fp.py")], cwd=staged,
                       check=True, stdout=subprocess.DEVNULL)
        replay = json.loads((staged / "out_fp_tail.json").read_text(encoding="utf-8"))
    compare(archived, replay)
    if args.capture:
        REPLAY.write_text(json.dumps(replay, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8", newline="\n")
    else:
        compare(json.loads(REPLAY.read_text(encoding="utf-8")), replay)
    print("PASS: 34,000 input rows, 26 source fit cells and all fields replayed")


if __name__ == "__main__":
    main()
