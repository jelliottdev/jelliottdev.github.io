"""Replay the pinned Round 19 G-FIX controls in a disposable source copy."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
OUTPUT = HERE / "replayed-out_fix.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Check saved receipts without decoding")
    parser.add_argument("--nproc", type=int, default=4)
    args = parser.parse_args()
    if args.check:
        subprocess.run([sys.executable, str(HERE / "check.py")], check=True)
        return
    if args.nproc < 1:
        parser.error("nproc must be positive")
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    for rel, digest in plan["source_files_sha256"].items():
        assert hashlib.sha256((SOURCE / rel).read_bytes()).hexdigest() == digest, rel
    with tempfile.TemporaryDirectory(prefix="round19-i1-fix-") as temporary:
        staged = Path(temporary) / "source"
        shutil.copytree(SOURCE, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        script = staged / "liber-primus/analysis/round19/I1/run_gates.py"
        subprocess.run([sys.executable, "-u", str(script), "--stage", "fix",
                        "--nproc", str(args.nproc), "--nseed", "7",
                        "--out", "replayed-out_fix.json"], check=True)
        made = script.parent / "replayed-out_fix.json"
        assert made.is_file()
        shutil.copyfile(made, OUTPUT)
    subprocess.run([sys.executable, str(HERE / "check.py")], check=True)


if __name__ == "__main__":
    main()
