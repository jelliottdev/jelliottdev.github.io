"""Export archived grid entries as strings with one-based coordinates.

No numeral base, character ordering, or cipher interpretation is applied.
Run from any directory; the source root follows this script's location.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_ROWS = {"lp2-49": 10, "lp2-50": 13, "lp2-51": 9}


def report(root=ROOT):
    records, sources = [], []
    for page_id, expected in EXPECTED_ROWS.items():
        path = root / f"data/pages/{page_id}.json"
        source_bytes = path.read_bytes()
        page = json.loads(source_bytes)
        rows = []
        for line in page["raw"].splitlines():
            # Do not silently skip a damaged alphanumeric row.
            if not line or not line[0].isascii() or not line[0].isalnum():
                continue
            if not re.fullmatch(r"[0-9A-Za-z]{2}(?:-[0-9A-Za-z]{2}){7}/?", line):
                raise ValueError(f"{page_id}: malformed grid row: {line!r}")
            rows.append(line.removesuffix("/").split("-"))
        if len(rows) != expected:
            raise ValueError(f"{page_id}: expected {expected} grid rows, got {len(rows)}")
        sources.append({
            "page": page_id,
            "path": f"data/pages/{page_id}.json",
            "record_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "transcription_sha256": page["transcription_sha256"],
            "image_sha256": page["image_sha256"],
        })
        for row, values in enumerate(rows, 1):
            for column, token in enumerate(values, 1):
                records.append({
                    "page": page_id, "row": row, "column": column,
                    "sequence": len(records) + 1, "token": token,
                })
    return {
        "schema": 1,
        "scope": "Archived alphanumeric entries only; no decoding or glyph corrections.",
        "coordinates": "One-based grid rows and columns; runic rows are not counted.",
        "sequence": "One-based, left to right then top to bottom, pages 49, 50, 51. Export order is not a claimed cipher traversal.",
        "sources": sources,
        "inventory": inventory(records),
        "records": records,
    }


def inventory(records):
    """Count exact strings; sequence positions refer back to exported records."""
    positions = {}
    for record in records:
        positions.setdefault(record["token"], []).append(record["sequence"])
    frequencies = [
        {"token": token, "count": len(indices), "sequence_positions": indices}
        for token, indices in sorted(positions.items(), key=lambda item: (-len(item[1]), item[0]))
    ]
    return {
        "comparison": "Exact case-sensitive two-character strings, across all three pages.",
        "entries": len(records),
        "distinct_tokens": len(positions),
        "singleton_tokens": sum(len(indices) == 1 for indices in positions.values()),
        "repeated_tokens": sum(len(indices) > 1 for indices in positions.values()),
        "maximum_frequency": max((len(indices) for indices in positions.values()), default=0),
        "frequencies": frequencies,
    }


def csv_report(data):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["page", "row", "column", "sequence", "token"], lineterminator="\n")
    writer.writeheader()
    writer.writerows(data["records"])
    return output.getvalue()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "csv"), default="json")
    args = parser.parse_args()
    data = report()
    print(csv_report(data) if args.format == "csv" else json.dumps(data, ensure_ascii=False, indent=2), end="" if args.format == "csv" else "\n")
