"""Rerun pinned Stage Y without changing its checkout or original tables."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def tracked(clone: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(clone), "show", "HEAD:" + path])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clone", type=Path, help="Pinned Wulfic source checkout")
    args = parser.parse_args()
    clone = args.clone.resolve()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    commit = subprocess.check_output(["git", "-C", str(clone), "rev-parse", "HEAD"], text=True).strip()
    if commit != plan["source"]["commit"]:
        raise ValueError(f"source revision differs: {commit}")
    for path, expected in plan["source_files_sha256"].items():
        content = (clone / path).read_bytes() if (clone / path).exists() else tracked(clone, path)
        if sha(content) != expected:
            raise ValueError(f"source bytes differ: {path}")
    for file, field in (("tools/run_stage_y.py", "stage_y_sha256"),
                        ("tools/run_stage_r.py", "stage_r_sha256"),
                        ("tools/run_stage_x.py", "stage_x_sha256")):
        if sha((clone / file).read_bytes()) != plan["source"][field]:
            raise ValueError(f"source code differs: {file}")
    sys.path.insert(0, str(clone))
    from tools import run_stage_r as r
    from tools import run_stage_y as y
    with tempfile.TemporaryDirectory(prefix="liberpedia-stage-y-") as folder:
        temp = Path(folder)
        people = temp / "people_2014.md"
        people.write_bytes(tracked(clone, "reference/community/people_2014.md"))
        r.ONION_2_HEX_SOURCE = people
        y.RESULTS_PATH = temp / "stage_y_results.tsv"
        y.CONTROLS_PATH = temp / "stage_y_controls.tsv"
        sys.argv = ["run_stage_y"]
        code = y.main()
        if code != 0:
            raise ValueError(f"source Stage Y controls failed; exit {code}")
        for name, expected_field in (("stage_y_results.tsv", "source_results_sha256"),
                                     ("stage_y_controls.tsv", "source_controls_sha256")):
            actual = (temp / name).read_bytes()
            original = tracked(clone, "reference/findings/" + name)
            if sha(actual) != plan["source"][expected_field] or actual != original:
                raise ValueError(f"{name} differs from pinned source result")
            (HERE / ("source-" + name)).write_bytes(actual)
            print(f"{name}: {len(actual.splitlines())} rows byte-identical; sha256 {sha(actual)}", flush=True)


if __name__ == "__main__":
    main()
