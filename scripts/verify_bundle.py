"""Verify extracted bundle members against a local manifest; no files are changed."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def verify(manifest):
    manifest = Path(manifest).resolve()
    root = manifest.parent
    records = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(records, list) or not records:
        raise ValueError("Expected a nonempty bundle member list.")
    seen, checked, problems = set(), 0, []
    for record in records:
        name = record.get("path") if isinstance(record, dict) else None
        if not isinstance(name, str) or not name or "\\" in name or ":" in name:
            raise ValueError("Invalid member path in manifest.")
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or name in seen:
            raise ValueError("Unsafe or duplicate member path: " + name)
        seen.add(name)
        target = (root / name).resolve()
        if not target.is_relative_to(root):
            raise ValueError("Member resolves outside the extracted folder: " + name)
        size, digest = record.get("bytes"), record.get("sha256")
        if type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise ValueError("Invalid size or SHA-256 for " + name)
        if not target.is_file():
            problems.append(name + ": missing or not a regular file")
            continue
        try:
            actual_size = 0
            actual_hash = hashlib.sha256()
            with target.open("rb") as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    actual_size += len(chunk)
                    actual_hash.update(chunk)
            if actual_size != size or actual_hash.hexdigest() != digest.lower():
                problems.append(name + ": size or SHA-256 mismatch")
            else:
                checked += 1
        except OSError as error:
            problems.append(name + ": " + str(error))
    return checked, problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path,
                        help="Manifest in the extraction root, e.g. REFERENCE-DATA-CONTENTS.json")
    args = parser.parse_args()
    try:
        checked, problems = verify(args.manifest)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for problem in problems:
        print("FAIL:", problem)
    print(f"{checked} files match the manifest; {len(problems)} problems.")
    print("Unlisted files are not checked. A match does not authenticate the manifest.")
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
