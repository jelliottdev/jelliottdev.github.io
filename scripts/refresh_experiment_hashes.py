"""Check or refresh declared file hashes. This does not execute or certify a test."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def digest(root, name):
    if not isinstance(name, str) or not name or "\\" in name:
        raise ValueError("Use a repository-relative file path")
    path = (root / name).resolve()
    if Path(name).is_absolute() or not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Invalid declared input or output: {name}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def refresh(root, identifier, write=False):
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", identifier):
        raise ValueError("Use an experiment ID, not a path")
    path = root / "experiments/records" / identifier / "record.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    if record["id"] != identifier:
        raise ValueError("Record ID does not match its folder")
    reproduction = record["reproduction"]
    changes = []
    actual = digest(root, reproduction["script"])
    if reproduction.get("script_sha256") != actual:
        changes.append(reproduction["script"])
        reproduction["script_sha256"] = actual
    for role in ("inputs", "outputs"):
        for entry in reproduction[role]:
            actual = digest(root, entry["path"])
            if entry.get("sha256") != actual:
                changes.append(entry["path"])
                entry["sha256"] = actual
    if write:
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="+")
    parser.add_argument("--write", action="store_true", help="Refresh only hashes; never alter findings or review status")
    args = parser.parse_args()
    failed = False
    for identifier in args.ids:
        changes = refresh(ROOT, identifier, args.write)
        failed |= bool(changes)
        verb = "refreshed" if args.write else "mismatched"
        print(f"{identifier}: {len(changes)} {verb} declared files")
    if failed and not args.write:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
