"""Repeat the source-derived complete singleton constraint grid."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def call(*args: str) -> None:
    subprocess.run(args, check=True, cwd=HERE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="independent saved-output check without rescan")
    args = parser.parse_args()
    if args.check:
        call(sys.executable, str(HERE / "check.py"))
        return
    exe = HERE / ("scan.exe" if os.name == "nt" else "scan")
    call("g++", "-O3", "-std=c++17", str(HERE / "scan.cpp"), "-o", str(exe))
    call(sys.executable, str(HERE / "prepare.py"))
    call(sys.executable, str(HERE / "controls.py"))
    call(str(exe), str(HERE / "scan-input.txt"), str(HERE / "spot-summary.tsv"), "100")
    call(str(exe), str(HERE / "scan-input.txt"), str(HERE / "full-summary.tsv"))
    call(sys.executable, str(HERE / "finalize.py"))
    call(sys.executable, str(HERE / "check.py"))


if __name__ == "__main__":
    main()
