"""Run the pinned D-04 source's full default three-page coefficient grid."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    root = args.source_root.resolve()
    if subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip() != plan["source_revision"]:
        raise ValueError("Pinned revision differs")
    lp = root / "liber-primus"
    for rel, expected in plan["source_sha256"].items():
        if sha(lp / rel) != expected:
            raise ValueError(f"Pinned input differs: {rel}")
    missing = lp / "data/keys/campaign12/walden.txt"
    if missing.exists():
        raise ValueError("Optional source bigram input unexpectedly present")
    source = lp / "analysis/campaign18_skip/ctfeedback_coeffs.py"
    command = [sys.executable, "-u", str(source), "--pages", "0,5,20"]
    env = dict(os.environ, PYTHONUTF8="1")
    target = HERE / "source-replay-stdout.txt"
    print(f"Running {plan['source_domain']['total_decodes']:,} source decodes; streaming to {target}", flush=True)
    with target.open("w", encoding="utf-8", newline="\n") as out:
        proc = subprocess.Popen(command, cwd=lp, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True, encoding="utf-8")
        for line in proc.stdout:
            out.write(line)
            out.flush()
            print(line, end="", flush=True)
        status = proc.wait()
    if status:
        raise RuntimeError(f"Pinned source process exited {status}; see {target}")
    print("Saved source stdout sha256", sha(target), flush=True)


if __name__ == "__main__":
    main()
