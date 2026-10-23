"""Run the pinned Campaign XVIII payload branch without changing its source.

The independent full-cell reconstruction is check.py. This script reproduces
the source's own console report in a disposable copy of its exact inputs.
"""
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="compare with the pinned source log")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="liberpedia-payload-skip-") as temporary:
        isolated = Path(temporary) / "liber-primus"
        shutil.copytree(HERE / "source", isolated)
        env = dict(os.environ, PYTHONUTF8="1")
        finished = subprocess.run(
            [sys.executable, str(isolated / "analysis/campaign18_skip/payload_skip.py")],
            cwd=isolated,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
    report = finished.stdout.strip()
    if args.check:
        archived = (HERE / "source/analysis/campaign18_skip/RUN-payload-skip.log").read_text(encoding="utf-8").strip()
        assert report == archived, (report, archived)
        result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        assert result["case_count"] == 880 and result["hit_count"] == 0
        assert abs(result["best"]["score"] + 6.756086107528059) < 1e-12
        print("PASS: unchanged source program reproduces its pinned log and saved best result")
    else:
        print(report)


if __name__ == "__main__":
    main()
