"""Re-run the published multi-history feedback grid and its planted controls."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import check

HERE = Path(__file__).resolve().parent
LANE = HERE / "source/analysis/round12/C1"


def run_controls(lane: Path, control_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("source_c1_control", lane / "control.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    passed = module.run()
    if not passed:
        raise RuntimeError("The 21 planted feedback controls did not pass")
    control_score = module.fb.score_norm(module.eng_to_idx(module.PLAIN))
    control_path.write_text(
        json.dumps({"source_controls": 21, "history_sources": 3,
                    "functions": 7, "k": 3, "all_passed": True,
                    "english_score": round(control_score, 4)}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    # Source results contain elapsed time. Replaying in place would overwrite
    # the published, hashed evidence even when the substantive result agrees.
    with tempfile.TemporaryDirectory(prefix="liberpedia-feedback-") as folder:
        root = Path(folder) / "source"
        shutil.copytree(HERE / "source", root)
        lane = root / "analysis/round12/C1"
        control_path = Path(folder) / "controls.json"
        run_controls(lane, control_path)
        subprocess.run([sys.executable, str(lane / "sweep.py")],
                       check=True, cwd=root)
        check.OUT = lane / "results.json"
        check.TEXT = root / "data/krisyotam_runes.txt"
        check.QGRAM = root / "data/english_quadgrams.txt"
        check.CONTROL = control_path
        print(json.dumps(check.verify(), indent=2))


if __name__ == "__main__":
    main()
