"""Rerun the three unchanged Campaign VII numeric-key source programs."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROGRAMS = ("b1_mayan", "b4_hash_kdf", "c2_cuneiform")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare with archived source JSON")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="liberpedia-c7-numeric-") as temp:
        isolated = Path(temp) / "liber-primus"
        shutil.copytree(HERE / "source", isolated)
        for name in PROGRAMS:
            path = isolated / "analysis/campaign7" / f"{name}.py"
            subprocess.run([sys.executable, str(path)], cwd=isolated,
                           env={**os.environ, "PYTHONUTF8": "1"},
                           check=True, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True, encoding="utf-8")
            produced = json.loads((path.parent / f"{name}_results.json").read_text(encoding="utf-8"))
            archived = json.loads((HERE / "source/analysis/campaign7" / f"{name}_results.json").read_text(encoding="utf-8"))
            if args.check:
                assert produced == archived, name
                print(f"PASS: {name} reproduces its pinned archived result")
            else:
                print(json.dumps(produced, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
