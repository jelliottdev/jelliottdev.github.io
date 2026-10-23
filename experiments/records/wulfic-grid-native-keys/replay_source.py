"""Optionally rerun the original pinned Stage N into a temporary directory."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
SCRIPT_SHA = "b3445d5e04eea89865898f8eafa40b2d5abd7948fb1f4e1b2b667a63a5f1a5c4"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--verify-output-dir", type=Path)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() == COMMIT
    assert sha(source / "tools/run_stage_n.py") == SCRIPT_SHA

    def verify(folder: Path) -> None:
        assert sha(folder / "stage_n_results.tsv") == sha(HERE / "source-stage_n_results.tsv")

    if args.verify_output_dir:
        verify(args.verify_output_dir.resolve())
    else:
        with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-stage-n-") as directory:
            folder = Path(directory)
            code = ("from pathlib import Path; import tools.run_stage_n as m; "
                    "m.OUT_PATH=Path(__import__('sys').argv[1])/'stage_n_results.tsv'; "
                    "raise SystemExit(m.main())")
            subprocess.run([sys.executable, "-c", code, str(folder)], cwd=source, check=True)
            verify(folder)
    print("Pinned Stage N source output reproduced byte-for-byte: OK")
