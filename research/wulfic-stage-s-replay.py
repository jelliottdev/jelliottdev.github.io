"""Run pinned Wulfic Stage S unchanged, writing only to an external directory.

This is an internal source-reconciliation helper. It does not turn the source's
invalid negative-control gate into a valid exclusion.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

PIN = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if actual != PIN:
        raise SystemExit(f"source revision mismatch: {actual}")
    output.mkdir(parents=True, exist_ok=True)
    if source == output or source in output.parents:
        raise SystemExit("output must be outside pinned source checkout")
    sys.path.insert(0, str(source))
    from tools import run_stage_s as stage  # type: ignore

    stage.OUT_PATH = output / "stage_s_candidates.tsv"
    stage.CONTROLS_PATH = output / "stage_s_controls.tsv"
    stage.WORKERS = 6  # Scheduling only; source rules, seeds and scoring are unchanged.
    sys.argv = ["run_stage_s"]
    status = stage.main()
    for name in ("stage_s_candidates.tsv", "stage_s_controls.tsv"):
        path = output / name
        data = path.read_bytes()
        print(name, "bytes", len(data), "sha256", hashlib.sha256(data).hexdigest(), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
