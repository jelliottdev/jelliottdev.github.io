"""Pin exact source Git objects and align their rune streams to current pages."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"


def git_bytes(source_root: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source_root), "show", f"{COMMIT}:{path}"])


def build(source_root: Path) -> dict:
    source_path = "tools/legacy/p21_30_second_layer.py"
    source = git_bytes(source_root, source_path)
    blob = subprocess.check_output(["git", "-C", str(source_root), "hash-object", "--stdin"], input=source).decode().strip()
    assert blob == "1e93873d5794bb1149826adc79c14cc76c4c830d"
    pages = []
    for old in range(21, 31):
        path = f"pages/page_{old:02d}/runes.txt"
        raw = git_bytes(source_root, path)
        text = raw.decode("utf8")
        values = [RUNES.index(ch) for ch in text if ch in RUNES]
        current_id = f"lp2-{old-17:02d}"
        current_path = ROOT / "data" / "pages" / f"{current_id}.json"
        current_raw = json.loads(current_path.read_text(encoding="utf8"))["raw"]
        current_values = [RUNES.index(ch) for ch in current_raw if ch in RUNES]
        assert values == current_values
        pages.append({"source_page": old, "current_page": current_id, "source_path": path,
                      "source_sha256": hashlib.sha256(raw).hexdigest(),
                      "source_blob": subprocess.check_output(["git", "-C", str(source_root), "hash-object", "--stdin"], input=raw).decode().strip(),
                      "current_path": f"data/pages/{current_id}.json", "current_sha256": hashlib.sha256(current_path.read_bytes()).hexdigest(),
                      "rune_count": len(values), "F_count": values.count(0),
                      "raw": text})
    return {"schema": "wulfic-p21-inputs-v1", "commit": COMMIT, "script_path": source_path,
            "script_blob": blob, "script_sha256": hashlib.sha256(source).hexdigest(), "pages": pages}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raw = json.dumps(build(args.source_root), ensure_ascii=False, indent=2).encode("utf8") + b"\n"
    out = HERE / "inputs.json"
    if args.check:
        assert out.read_bytes() == raw
    else:
        out.write_bytes(raw)
    print("All ten pinned page streams match LP2-04–13 rune for rune.")


if __name__ == "__main__":
    main()
