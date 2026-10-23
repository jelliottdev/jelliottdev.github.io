"""Run F-01 in a temporary source copy, keeping archived evidence unchanged."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from check import verify

HERE = Path(__file__).resolve().parent


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="liberpedia-f01-") as folder:
        root = Path(folder) / "source"
        shutil.copytree(HERE / "source", root)
        script = root / "liber-primus/analysis/round16/F-01/sweep.py"
        subprocess.run([sys.executable, str(script)], check=True, cwd=root)
        print(json.dumps(verify(script.parent / "results.json"), indent=2))


if __name__ == "__main__":
    main()
