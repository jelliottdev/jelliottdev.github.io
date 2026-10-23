"""Replay the pinned A-04 programs in a disposable source-shaped directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "replay-plan.json").read_text(encoding="utf-8"))
SOURCE = HERE / "source" / "liber-primus"
PROGRAMS = SOURCE / "analysis" / "round18" / "L5-payload"
OUTPUT_NAMES = ["grid.json", "calibration.json", "glyphmatch.json", "pixelmatch.json", "adjudication.json"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image-dir", type=Path, default=HERE.parents[2] / "images")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    for name, want in PLAN["image_sha256"].items():
        path = args.image_dir / name
        assert sha(path) == want, (path, "image bytes differ from pinned source")
    with tempfile.TemporaryDirectory(prefix="liberpedia-a04-") as td:
        root = Path(td)
        dst = root / "liber-primus"
        shutil.copytree(SOURCE, dst)
        img = dst / "data" / "relikd"
        img.mkdir(parents=True)
        for n in (49, 50, 51):
            shutil.copyfile(args.image_dir / f"lp2-{n}.jpg", img / f"p{n}.jpg")
        work = dst / "analysis" / "round18" / "L5-payload"
        logs = {}
        for program in PLAN["source_programs"]:
            p = subprocess.run([sys.executable, str(work / program)], cwd=work,
                               capture_output=True, text=True, check=True)
            logs[program] = p.stdout[-10000:]
        out = HERE / "replay-output"
        out.mkdir(exist_ok=True)
        for name in OUTPUT_NAMES:
            shutil.copyfile(work / name, out / name)
        (out / "source-stdout.json").write_text(json.dumps(logs, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.check:
        subprocess.run([sys.executable, str(HERE / "check.py")], check=True)


if __name__ == "__main__":
    main()
