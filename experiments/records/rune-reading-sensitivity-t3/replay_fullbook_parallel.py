"""Replay independent T3 decoder levels in parallel without changing source code.

Each level runs the exact archived t3_decode.py in a separate temporary source
tree. The source resets its replicate seeds at every level, so the resulting
rows can be merged in the declared order. Source timings vary and are not a
scientific output. The exact KJV input is shared as a read-only hard link.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
KJV = REPO / "experiments/records/dukotah-offset-model-integrity/source-kjv.txt"
KJV_SHA = "0f1a83cbcdc1d3fae6bcc3daaa496d4fa723fcce9526e84e20df12ae33fda986"
SOURCE_REL = Path("liber-primus/analysis/round19/T3")
SOURCE_SCRIPT_SHA = "2bf593acdd73b1f7f6132fadf50c7f5ea10ecec399c97b2a35987282d312889c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def same(a, b, where="root"):
    """Compare scientific fields exactly up to source floating-point tolerance."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and set(a) == set(b), where
        for key in a:
            if key != "secs":
                same(a[key], b[key], where + "." + key)
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b), where
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, f"{where}[{i}]")
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        assert isinstance(b, (int, float)) and math.isclose(a, b, abs_tol=1e-12, rel_tol=1e-12), (where, a, b)
    else:
        assert a == b, (where, a, b)


def run_level(level: int, length: int, reps: int, register: str):
    with tempfile.TemporaryDirectory(prefix=f"liberpedia-t3-k{level}-") as temp:
        root = Path(temp)
        with zipfile.ZipFile(HERE / "source-snapshot.zip") as archive:
            archive.extractall(root)
        t3 = root / SOURCE_REL
        assert sha(t3 / "t3_decode.py") == SOURCE_SCRIPT_SHA
        if register == "KJV":
            assert sha(KJV) == KJV_SHA
            target = root / "liber-primus/data/kjv.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.link(KJV, target)
            except OSError:
                shutil.copyfile(KJV, target)
            assert sha(target) == KJV_SHA
        env = os.environ.copy()
        env["T3_KBOOK"] = str(level)
        command = [sys.executable, "t3_decode.py", str(length), str(reps), register]
        completed = subprocess.run(command, cwd=t3, env=env, capture_output=True,
                                   text=True, check=True)
        path = t3 / f"out_decode_L{length}_{register}.json"
        output = json.loads(path.read_text(encoding="utf-8"))
        assert len(output["rows"]) == 1 and output["rows"][0]["k_book"] == level
        assert output["gate_F0"]["pass"] and output["gate_F0"]["path_mismatches"] == 0
        return output, completed.stdout


def run_all(levels: list[int], length: int, reps: int, register: str, jobs: int):
    assert levels and len(levels) == len(set(levels))
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        level_by_future = {pool.submit(run_level, level, length, reps, register): level
                           for level in levels}
        completed = {}
        for future in concurrent.futures.as_completed(level_by_future):
            level = level_by_future[future]
            completed[level] = future.result()[0]
            print(f"PASS source level k={level}", flush=True)
    first = completed[levels[0]]
    for level in levels[1:]:
        other = completed[level]
        assert set(first) == set(other)
        for key in first:
            if key not in {"rows", "K_REC_k_book", "K_SEP_k_book"}:
                same(first[key], other[key], key)
    merged = {**first, "rows": [completed[level]["rows"][0] for level in levels]}
    merged["K_REC_k_book"] = next((r["k_book"] for r in merged["rows"]
                                  if r["recovery_correct"]["median"] < 0.90), None)
    merged["K_SEP_k_book"] = next((r["k_book"] for r in merged["rows"]
                                  if not r["separated"]), None)
    return merged


def main():
    from run import verify_inputs
    verify_inputs()  # Validate the complete declared source archive before extracting it.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--length", type=int, default=12956)
    parser.add_argument("--reps", type=int, default=6)
    parser.add_argument("--register", choices=("LP1", "KJV"), default="KJV")
    parser.add_argument("--levels", default="0,50,100,200,450,900")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    assert 1 <= args.jobs <= 4 and args.length > 0 and args.reps > 0
    levels = [int(x) for x in args.levels.split(",")]
    assert all(0 <= x <= 12956 for x in levels)
    result = run_all(levels, args.length, args.reps, args.register, args.jobs)
    if args.compare:
        same(json.loads(args.compare.read_text(encoding="utf-8")), result)
        print("PASS source result comparison (excluding elapsed seconds)")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {args.output} with {len(result['rows'])} ordered levels")


if __name__ == "__main__":
    main()
