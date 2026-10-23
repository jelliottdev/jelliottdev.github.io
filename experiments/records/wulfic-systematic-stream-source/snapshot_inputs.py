"""Freeze the exact pinned source page bytes used by stream_cipher_attack.py."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
GP = {r: i for i, r in enumerate(RUNES)}
SEPS = set(".-• \n")
COMMIT = "bf89d3d13aad2b8f2c95ab195cf1b092f250775c"


def words_from_source_text(text: str) -> list[list[int]]:
    words: list[list[int]] = []
    current: list[int] = []
    for char in text:
        if char in GP:
            current.append(GP[char])
        elif char in SEPS:
            if current:
                words.append(current)
                current = []
    if current:
        words.append(current)
    return words


def git_bytes(root: Path, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(root), "show", f"{COMMIT}:{path}"])


def build(source_root: Path) -> dict:
    source_path = "tools/legacy/stream_cipher_attack.py"
    source = git_bytes(source_root, source_path)
    source_blob = subprocess.check_output(["git", "-C", str(source_root), "hash-object", "--stdin"], input=source).decode().strip()
    assert source_blob == "0a588175f9a1b7537740803876d762ab542b50a7"
    pages = []
    excluded = {1, *range(3, 18)}
    for ordinal in range(56):
        if ordinal in excluded:
            continue
        path = f"pages/page_{ordinal:02d}/runes.txt"
        raw = git_bytes(source_root, path)
        words = words_from_source_text(raw.decode("utf-8"))
        values = [v for word in words for v in word]
        if len(values) < 10:
            continue
        assert 18 <= ordinal <= 55
        pages.append({
            "source_ordinal": ordinal,
            "page": f"lp2-{ordinal-17:02d}",
            "source_path": path,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "values": values,
            "word_lengths": [len(word) for word in words],
        })
    assert len(pages) == 38
    return {"schema": "wulfic-systematic-stream-inputs-v1", "source_commit": COMMIT,
            "source_script_blob": source_blob, "pages": pages}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = HERE / "inputs.json"
    new = json.dumps(build(args.source_root), ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    if args.check:
        assert target.read_bytes() == new
        print("Pinned input snapshot matches source Git objects.")
    else:
        target.write_bytes(new)
        print(f"Wrote {target} ({len(new)} bytes).")


if __name__ == "__main__":
    main()
