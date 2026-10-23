"""Run three pinned QuagMirror drafts without changing their fixed stopping rules."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
NAMES = ("OG_quag_mirror.py", "quag_mirror_v4.py", "quag_mirror_WIP.py")


def constants(path: Path) -> dict:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    wanted = {"section1", "section1_spaces", "latin_fragments", "runes"}
    return {node.targets[0].id: ast.literal_eval(node.value)
            for node in tree.body if isinstance(node, ast.Assign)
            and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id in wanted}


def table(stdout: str, label: str) -> list[int]:
    rows = [line for line in stdout.splitlines() if line.startswith(label)]
    if len(rows) != 1:
        raise ValueError(f"Expected one {label} output row; saw {len(rows)}")
    return [int(value) for value in re.findall(r"\|\s*(\d+)\s*", rows[0])]


def execute(name: str) -> dict:
    path = SOURCE / name
    fixed = constants(path)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run([sys.executable, str(path)], cwd=SOURCE, env=env,
                               capture_output=True, text=True, encoding="utf-8", check=True)
    stdout = completed.stdout.replace("\r\n", "\n")
    lines = stdout.splitlines()
    if len(lines) < 3 or lines[-1] != "-" * 57 or lines[-3] != "-" * 57:
        raise ValueError(f"Cannot locate fixed final output for {name}")
    final_text = lines[-2]
    ct = table(stdout, "[   CT Index   ]")
    at = table(stdout, "[   AT Index   ]")
    pt = table(stdout, "[   PT Index   ]")
    if not (len(ct) == len(at) == len(pt)):
        raise ValueError("Source output tables have different lengths")
    expected = "".join(fixed["latin_fragments"][value] +
                       (" " if i + 1 in fixed["section1_spaces"] else "")
                       for i, value in enumerate(pt))
    if expected.rstrip() != final_text.rstrip():
        raise ValueError("Printed transliteration differs from numeric output table")
    if ct != fixed["section1"][:len(ct)]:
        raise ValueError("Source processed different input than its declared section1")
    return {
        "source_file": name,
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source_input_length": len(fixed["section1"]),
        "positions_processed": len(pt),
        "ciphertext_indices": ct,
        "autokey_indices": at,
        "plaintext_indices": pt,
        "final_text": final_text,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
    }


def compute() -> dict:
    return {"source_commit": "88ef1e60b0738b8b28db96bc9dc44dc4da8dd307",
            "dependency": "sympy 1.14.0 or compatible sieve.mobiusrange",
            "variants": [execute(name) for name in NAMES]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the immutable checked result")
    args = parser.parse_args()
    result = compute()
    path = HERE / "results.json"
    if args.write:
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8", newline="\n")
    elif result != json.loads(path.read_text(encoding="utf-8")):
        raise SystemExit("Pinned source output differs from results.json")
    print(json.dumps({row["source_file"]: {"positions": row["positions_processed"],
                                           "opening": row["final_text"][:90]}
                      for row in result["variants"]}, indent=2))


if __name__ == "__main__":
    main()
