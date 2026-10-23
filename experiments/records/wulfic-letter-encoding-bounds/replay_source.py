"""Run only the two pinned Wulfic Q unittest classes from an external checkout.

The source test files are read from Git objects into a temporary test package;
unlicensed upstream code is not copied into the public experiment bundle.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

PIN = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
EXPECTED = {
    "tests/test_leak.py": "6896fb6ecd59fbfdc1aab7e1bf6c24064c23fc10275a02a7168f0a49cf3503e6",
    "tests/test_stats.py": "7d8ae3cadefed598f3b95da96f5bd69da21612e67b786104d29ac5a8c51c8fae",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip() != PIN:
        raise SystemExit("wrong upstream revision")
    if output == source or source in output.parents:
        raise SystemExit("test output must be outside upstream checkout")
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="liberpedia-wulfic-q-") as name:
        base = Path(name)
        tests = base / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("", encoding="utf-8", newline="\n")
        for rel, expected in EXPECTED.items():
            raw = subprocess.check_output(["git", "show", f"{PIN}:{rel}"], cwd=source)
            if hashlib.sha256(raw).hexdigest() != expected:
                raise AssertionError(f"upstream test changed: {rel}")
            (tests / Path(rel).name).write_bytes(raw)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(base) + os.pathsep + str(source)
        command = [sys.executable, "-m", "unittest", "-v",
                   "tests.test_leak.TestC3MarkerLetter", "tests.test_stats.TestHomophonic"]
        result = subprocess.run(command, cwd=source, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    (output / "source-tests.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
    print(result.stdout)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
