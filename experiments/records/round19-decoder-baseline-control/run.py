"""Replay the pinned Round 19 I1 baseline decoder-control grid without writing to source."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
DEFAULT_SOURCE = HERE / "source" / "liber-primus"
sys.dont_write_bytecode = True


def verify(source: Path) -> None:
    for rel, expected in PLAN["bundled_source_files_sha256"].items():
        actual = hashlib.sha256((source.parent / rel).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"Pinned input differs: {rel}: {actual}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--nproc", type=int, default=6)
    ap.add_argument("--check", action="store_true", help="verify saved results without rerunning the source")
    args = ap.parse_args()
    source = args.source_root.resolve()
    verify(source)
    if args.check:
        import check
        check.check()
        return
    # Source code and data run from a disposable copy; the exact archive remains untouched.
    with tempfile.TemporaryDirectory(prefix="liberpedia-i1-") as tmp:
        staged = Path(tmp)
        for rel in PLAN["bundled_source_files_sha256"]:
            target = staged / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source.parent / rel, target)
        sys.path.insert(0, str(staged / "liber-primus" / "analysis" / "round19" / "I1"))
        import run_gates as rg
        output_dir = staged / "output"
        output_dir.mkdir()
        rg.HERE = str(output_dir)
        rg.stage_base(args.nproc, 7)
        import check
        check.check(output_dir / "out_base.json")


if __name__ == "__main__":
    main()
