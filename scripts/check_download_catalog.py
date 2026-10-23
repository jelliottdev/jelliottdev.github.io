"""Verify catalog sizes and hashes against the exact published file bytes.

Run before export builders in CI, so stale hashes cannot be hidden by rebuilding.
Git line-ending checks are optional; the byte check also works in a static-site directory.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def portable_line_ending_errors(root, crlf_paths):
    """Catch files whose catalog hashes Windows CRLF but Git publishes LF."""
    if not crlf_paths or not (root / ".git").exists():
        return []
    try:
        result = subprocess.run(
            ["git", "check-attr", "-z", "--stdin", "text", "eol"],
            cwd=root, input=b"\0".join(name.encode("utf-8") for name in crlf_paths) + b"\0",
            capture_output=True, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    fields = result.stdout.split(b"\0")
    attrs = {}
    for i in range(0, len(fields) - 2, 3):
        name = fields[i].decode("utf-8")
        attrs.setdefault(name, {})[fields[i + 1]] = fields[i + 2]
    errors = []
    for name, item in attrs.items():
        if item.get(b"text") in (b"set", b"auto") and item.get(b"eol") == b"lf":
            errors.append(f"Git normalizes CRLF after catalog hashing: {name}")
    return errors


def verify_scopes(root, records):
    """Check download discovery metadata against the data each file contains."""
    index = json.loads((root / "data/index.json").read_text(encoding="utf-8"))
    releases = {page["id"]: page["release"] for page in index["pages"]}
    by_path = {record["path"]: record for record in records}
    errors = []
    groups = [
        ("exports/alphanumeric-grids.json", ["exports/alphanumeric-grids.json",
         "exports/alphanumeric-grids.csv", "scripts/export_alphanumeric_grids.py"]),
        ("data/evidence/rune-ioc.json", ["data/evidence/rune-ioc.json", "exports/rune-ioc.csv"]),
        ("data/evidence/known-reading-page-sums.json", ["data/evidence/known-reading-page-sums.json",
         "exports/known-reading-page-sums.csv"]),
    ]
    for source, paths in groups:
        data = json.loads((root / source).read_text(encoding="utf-8"))
        expected_pages = {item["page"] for item in data["records"]}
        for name in paths:
            record = by_path.get(name, {})
            pages = record.get("pages", [])
            if set(pages) != expected_pages or len(pages) != len(set(pages)):
                errors.append(f"Download page scope differs from {source}: {name}")
            expected_releases = {releases[page] for page in expected_pages}
            actual_releases = set(record.get("releases", []))
            if record.get("release"):
                actual_releases.add(record["release"])
            if actual_releases != expected_releases:
                errors.append(f"Download release scope differs from {source}: {name}")
    panel = json.loads((root / "exports/lp2-15-differences.json").read_text(encoding="utf-8"))
    page = Path(panel["source"]).stem
    for extension in ("json", "csv"):
        name = f"exports/lp2-15-differences.{extension}"
        record = by_path.get(name, {})
        if record.get("page") != page or record.get("release") != releases[page]:
            errors.append(f"Download scope differs from number-panel source: {name}")
    return errors


def verify(root):
    records = json.loads((root / "data/catalog.json").read_text(encoding="utf-8"))["files"]
    errors = []
    seen = set()
    crlf_paths = []
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
        if b"\r\n" in data:
            crlf_paths.append(name)
        if len(data) != record["bytes"] or hashlib.sha256(data).hexdigest() != record["sha256"]:
            errors.append(f"Published bytes differ from catalog: {name}")
    errors.extend(portable_line_ending_errors(root, crlf_paths))
    errors.extend(verify_scopes(root, records))
    return len(records), errors


if __name__ == "__main__":
    count, errors = verify(ROOT)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(1)
    print(f"PASS: all {count} catalog files match their published sizes and SHA-256 hashes; dataset scopes match source records")
