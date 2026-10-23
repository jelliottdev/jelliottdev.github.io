"""Replay the pinned source without changing its algorithm or checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SOURCE_FILES = {
    "analysis/recon/i6_mdl/mdl_test.py": "ca501ba03dc9ca4de0fb7c32c2d46f85aa3794d8d18f534d6b5c1499945bdb38",
    "data/krisyotam_runes.txt": "5e0003aa7f7dde3b238d17c5f964790dbf6bf9db5edacc4a5ec0bad81c6f4bce",
    "src/lp/gematria.py": "7b4f5c30137741ab3c33638fb91076c4b1f228229dc3634ba2e6ef232cd47f04",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True,
                        help="Pinned f08b20b Dukotah checkout")
    args = parser.parse_args()
    root = args.source_root.resolve() / "liber-primus"
    for rel, digest in SOURCE_FILES.items():
        if sha(root / rel) != digest:
            raise ValueError(f"Pinned source differs: {rel}")
    with tempfile.TemporaryDirectory(prefix="mdl-source-replay-") as temp:
        staged = Path(temp) / "liber-primus"
        for rel in SOURCE_FILES:
            target = staged / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / rel, target)
        script = staged / "analysis/recon/i6_mdl/mdl_test.py"
        proc = subprocess.run([sys.executable, str(script)], cwd=staged,
                              capture_output=True, text=True, check=True)
        fresh = json.loads((script.parent / "mdl_result.json").read_text(encoding="utf-8"))
        published = json.loads((HERE / "source-mdl_result.json").read_text(encoding="utf-8"))
        if fresh != published:
            raise AssertionError("Fresh source output differs from archived numeric result")
        (HERE / "replayed-mdl_result.json").write_text(
            json.dumps(fresh, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"PASS: unchanged source output matches all {len(fresh)} top-level fields")
        print(proc.stdout.splitlines()[-4:])


if __name__ == "__main__":
    main()
