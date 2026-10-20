"""Compare an existing file's exact bytes with the LP2-56 target using SHA-512.

This assumes SHA-512; the manuscript does not name the algorithm.
No network access, text normalization, or file writes are performed.
Exit status: 0 match, 1 mismatch, 2 invalid input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def target_record(root=ROOT):
    path = root / "data/pages/lp2-56.json"
    raw = path.read_bytes()
    page = json.loads(raw)
    if not isinstance(page, dict) or page.get("id") != "lp2-56":
        raise ValueError("Target record must identify page lp2-56")
    reading = page.get("reading")
    if not isinstance(reading, dict) or not isinstance(reading.get("literal"), str):
        raise ValueError("Target record must contain a literal reading as text")
    rows = [
        line.rstrip("/")
        for line in reading["literal"].splitlines()
        if re.fullmatch(r"[0-9a-f]+/?", line)
    ]
    target = "".join(rows)
    if len(rows) != 5 or len(target) != 128:
        raise ValueError("Expected five hexadecimal rows totalling 128 characters")
    return target, hashlib.sha256(raw).hexdigest()


def compare_file(path, target, record_hash):
    sha512, sha256 = hashlib.sha512(), hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            size += len(chunk)
            sha512.update(chunk)
            sha256.update(chunk)
    return {
        "candidate_file": str(path),
        "candidate_bytes": size,
        "candidate_sha256": sha256.hexdigest(),
        "algorithm_assumption": "SHA-512",
        "input_rule": "Exact file bytes, no decoding or normalization",
        "candidate_sha512": sha512.hexdigest(),
        "target_page": "lp2-56",
        "target_record_sha256": record_hash,
        "target_digest": target,
        "matches": sha512.hexdigest() == target,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="Existing local file to read")
    args = parser.parse_args()
    try:
        target, record_hash = target_record()
        result = compare_file(args.candidate, target, record_hash)
    except (OSError, ValueError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))
    return 0 if result["matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
