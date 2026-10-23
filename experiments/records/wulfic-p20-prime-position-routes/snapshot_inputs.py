"""Freeze source page and relocated Deor bytes without copying the poem."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
GP = {r: i for i, r in enumerate(RUNES)}


def git_bytes(root: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{COMMIT}:{path}"])


def build(root: Path) -> dict:
    raw = git_bytes(root, "pages/page_20/runes.txt")
    poem = git_bytes(root, "data/corpora/deor_poem.txt")
    source = git_bytes(root, "tools/legacy/solve_p20.py")
    blob = subprocess.check_output(["git", "-C", str(root), "hash-object", "--stdin"], input=source).decode().strip()
    assert blob == "05a7d226dab2ffb4ad3f324039ae0c8d56e639ab"
    values = [GP[c] for c in raw.decode("utf8") if c in GP]
    assert len(values) == 217
    deor = [ord(c) - ord("a") for c in poem.decode("utf8").lower() if c.isalpha()]
    assert len(deor) >= 170
    return {"schema": "wulfic-p20-route-inputs-v1", "source_commit": COMMIT,
            "source_blob": blob, "page": "lp2-03", "source_page": "pages/page_20/runes.txt",
            "source_page_sha256": hashlib.sha256(raw).hexdigest(),
            "source_deor": "data/corpora/deor_poem.txt",
            "source_deor_sha256": hashlib.sha256(poem).hexdigest(),
            "values": values, "deor_key_prefix": deor[:170],
            "source_deor_alpha_count": len(deor)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = json.dumps(build(args.source_root), ensure_ascii=False, indent=2).encode("utf8") + b"\n"
    target = HERE / "inputs.json"
    if args.check:
        assert target.read_bytes() == output
        print("Source byte snapshot verified.")
    else:
        target.write_bytes(output)
        print("Source byte snapshot written.")


if __name__ == "__main__":
    main()
