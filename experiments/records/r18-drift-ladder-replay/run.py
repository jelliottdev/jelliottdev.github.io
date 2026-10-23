"""Replay the pinned B4/B5 source in a disposable checkout made from hashed files."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LP = Path("liber-primus")
FOLDER = Path("analysis/round18/L2-filter-leak")
OUTPUTS = {
    "gate": "gate_F0.json",
    "b4pc": "b4_control.json",
    "ladder": "b4_ladder.json",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--kjv", type=Path, required=True)
    parser.add_argument("--stage", choices=OUTPUTS, required=True)
    parser.add_argument("--nproc", type=int, default=6)
    parser.add_argument("--resume-from", type=Path,
                        help="Existing checkpoint; rows with source import errors are retried")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    root = args.source_root.resolve()
    kjv = args.kjv.resolve()
    revision = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if revision != plan["source_revision"]:
        raise ValueError("Source revision differs from frozen plan")
    if sha(kjv) != plan["external_kjv_sha256"]:
        raise ValueError("KJV bytes differ from frozen plan")
    for rel, expected in plan["source_input_sha256"].items():
        if sha(root / LP / rel) != expected:
            raise ValueError(f"Source input differs: {rel}")
    for name, expected in plan["source_result_sha256"].items():
        if sha(root / LP / FOLDER / name) != expected:
            raise ValueError(f"Source receipt differs: {name}")
    amendment = json.loads((HERE / "plan-amendment.json").read_text(encoding="utf-8"))
    derived = (HERE.parents[2] / amendment["source_path"]).resolve()
    if sha(derived) != amendment["sha256"] or derived.stat().st_size != amendment["bytes"]:
        raise ValueError("Derived PRNG ciphertext input differs from amendment")
    with tempfile.TemporaryDirectory(prefix="r18-ladder-") as temp:
        stage = Path(temp) / LP
        for rel in plan["source_input_sha256"]:
            dest = stage / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / LP / rel, dest)
        dest = stage / "data/kjv.txt"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(kjv, dest)
        dependency = stage / amendment["stage_path"]
        dependency.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(derived, dependency)
        folder = stage / FOLDER
        if args.stage == "ladder" and args.resume_from:
            prior = json.loads(args.resume_from.resolve().read_text(encoding="utf-8"))
            kept = [r for r in prior["rows"] if "error" not in r]
            if len(kept) != 210 or any(r.get("n_decodes") != 5961 for r in kept):
                raise ValueError("Resume checkpoint is not the expected 210 completed rows")
            prior["rows"] = kept
            (folder / "b4_ladder.json").write_text(json.dumps(prior, indent=1), encoding="utf-8")
        env = dict(os.environ, PYTHONUTF8="1")
        if args.stage == "gate":
            command = [sys.executable, str(folder / "fastbeam.py")]
        else:
            command = [sys.executable, str(folder / "b4_ladder.py"), "--stage", args.stage]
            if args.stage == "ladder":
                command += ["--cands", "400", "--nproc", str(args.nproc)]
        print("Running", " ".join(command), flush=True)
        subprocess.run(command, cwd=folder, env=env, check=True)
        output = folder / OUTPUTS[args.stage]
        receipt = HERE / ("replayed-" + OUTPUTS[args.stage])
        receipt.write_bytes(output.read_bytes())
    print("Saved", receipt, "sha256", sha(receipt), flush=True)


if __name__ == "__main__":
    main()
