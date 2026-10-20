"""Verify catalog sizes and hashes against the exact published file bytes.

Run before export builders in CI, so stale hashes cannot be hidden by rebuilding.
No Git dependency: works in a checkout or a complete static-site directory.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def verify(root):
    records = json.loads((root / "data/catalog.json").read_text(encoding="utf-8"))["files"]
    errors = []
    seen = set()
    for record in records:
        name = record["path"]
        path = (root / name).resolve()
        if name in seen:
            errors.append(f"Duplicate catalog path: {name}")
        seen.add(name)
        if not path.is_relative_to(root.resolve()):
            errors.append(f"Path escapes site: {name}")
            continue
        if not path.is_file():
            errors.append(f"Missing file: {name}")
            continue
        data = path.read_bytes()
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            errors.append(f"Published bytes differ from catalog: {name}")
    return len(records), errors


if __name__ == "__main__":
    count, errors = verify(ROOT)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"PASS: all {count} catalog files match their published sizes and SHA-256 hashes")
