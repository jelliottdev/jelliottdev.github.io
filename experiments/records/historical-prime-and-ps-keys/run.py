"""Execute the pinned B3 program in isolation and verify the archived result."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from check import analyze

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source/liber-primus"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="liberpedia-b3-") as folder:
        work = Path(folder) / "liber-primus"
        shutil.copytree(SOURCE, work)
        script = work / "analysis/campaign7/b3_hints.py"
        subprocess.run([sys.executable, str(script)], cwd=work, check=True)
        replay = json.loads((script.parent / "b3_hints_results.json").read_text(encoding="utf-8"))
        source = json.loads((SOURCE / "analysis/campaign7/original_results.json").read_text(encoding="utf-8"))
        assert replay == source, "Pinned B3 output changed"
    cases, report = analyze()
    assert len(cases) == 4032 and report["source_result_match"]
    print("PASS: exact source B3 output, all 4,032 independently scored cases, two planted controls")


if __name__ == "__main__":
    main()
