"""Compare archived seventh-onion transcription text with wiki LP2 text.

This checks source files and differences; it does not choose a correct glyph.
Run from any directory:
  python scripts/audit_seventh_onion_transcriptions.py --check
"""

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

from audit_2014_seventh_onion import ROOT, SOURCE, sources

REPORT = ROOT / "exports/seventh-onion-transcription-variants.json"
CSV = ROOT / "exports/seventh-onion-transcription-pages.csv"
GRID_CSV = ROOT / "exports/seventh-onion-grid-variants.csv"
RUNE = re.compile(r"[\u16a0-\u16ff]")
GRID_ROW = re.compile(r"[0-9A-Za-z]{2}(?:[\t -]+[0-9A-Za-z]{2}){7}/?")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def page_texts(files):
    combined = files["0-55.jpg.runes.txt"].decode("utf-8")
    blocks = re.split(r"(?m)^%\s*$", combined)
    if len(blocks) != 56:
        raise ValueError(f"Expected 56 source blocks, found {len(blocks)}")
    return [block.strip("\r\n") for block in blocks] + [
        files[f"{i}.jpg.runes.txt"].decode("utf-8").strip("\r\n") for i in (56, 57)
    ]


def grid(text, expected_rows):
    rows = []
    for line in text.splitlines():
        if GRID_ROW.fullmatch(line):
            rows.append(re.split(r"[\t -]+", line.rstrip("/")))
    if len(rows) != expected_rows or any(len(row) != 8 for row in rows):
        raise ValueError(f"Unexpected grid dimensions: {len(rows)} rows")
    return rows


def csv_bytes(rows, fields):
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def audit():
    manifest, files = sources()
    archived = page_texts(files)
    pages, boundary_changes, grid_changes = [], [], []
    for i, source_text in enumerate(archived):
        page = f"lp2-{i:02}"
        current_file = ROOT / "text" / f"{page}.txt"
        current_bytes = current_file.read_bytes()
        current_text = current_bytes.decode("utf-8").strip("\r\n")
        source_runes = RUNE.findall(source_text)
        current_runes = RUNE.findall(current_text)
        record = json.loads((ROOT / "data/pages" / f"{page}.json").read_text(encoding="utf-8"))
        if source_runes != current_runes or len(current_runes) != record["rune_count"]:
            raise ValueError(f"Ordered rune stream differs: {page}")
        source_gaps = RUNE.split(source_text)
        current_gaps = RUNE.split(current_text)
        changes = []
        for ordinal, (before, after) in enumerate(zip(source_gaps, current_gaps)):
            if before != after:
                changes.append({"page": page, "before_rune_ordinal": ordinal,
                                "archived_between_runes": before, "wiki_between_runes": after})
        boundary_changes.extend(changes)
        if i in (49, 50, 51):
            source_rows = grid(source_text, {49: 10, 50: 13, 51: 9}[i])
            current_rows = grid(current_text, {49: 10, 50: 13, 51: 9}[i])
            for row, (source_cells, current_cells) in enumerate(zip(source_rows, current_rows), 1):
                for column, (left, right) in enumerate(zip(source_cells, current_cells), 1):
                    if left != right:
                        grid_changes.append({"page": page, "row": row, "column": column,
                                             "archive_token": left, "wiki_token": right})
        pages.append({"page": page, "rune_count": len(source_runes),
                      "archive_text_sha256": sha256(source_text.encode("utf-8")),
                      "wiki_file_sha256": sha256(current_bytes),
                      "exact_text_match_after_edge_newlines": source_text == current_text,
                      "ordered_runes_match": True, "non_rune_boundary_changes": len(changes),
                      "grid_token_changes": sum(x["page"] == page for x in grid_changes)})
    if (sum(row["exact_text_match_after_edge_newlines"] for row in pages), len(boundary_changes), len(grid_changes)) != (32, 36, 5):
        raise ValueError("Unexpected transcription difference counts")
    return {
        "schema": "liberpedia-seventh-onion-transcription-variants-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "comparison": "Archive 0-55, 56 and 57 rune text versus current wiki text/lp2-NN.txt; edge newlines removed for text comparison only.",
        "summary": {"pages": 58, "ordered_rune_stream_matches": 58,
                    "exact_text_matches": 32, "pages_with_non_rune_changes": 26,
                    "non_rune_boundary_changes": 36, "grid_token_changes": 5},
        "pages": pages, "non_rune_boundary_changes": boundary_changes,
        "grid_token_changes": grid_changes,
        "limits": [
            "A matching ordered rune stream does not settle word boundaries, punctuation, line breaks, printed number panels, or alphanumeric grid cells.",
            "The five grid-cell disagreements are recorded as variants, not visually adjudicated corrections.",
            "The archived possibilities files are generated candidate outputs; they are preserved as source context but are not established plaintext.",
            "The wiki text is a separate later compilation; neither source is authenticated as an error-free transcription of every visible mark.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit()
    encoded = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    pages = csv_bytes(report["pages"], ["page", "rune_count", "archive_text_sha256", "wiki_file_sha256",
                                          "exact_text_match_after_edge_newlines", "ordered_runes_match",
                                          "non_rune_boundary_changes", "grid_token_changes"])
    cells = csv_bytes(report["grid_token_changes"], ["page", "row", "column", "archive_token", "wiki_token"])
    if args.check and (REPORT.read_bytes() != encoded or CSV.read_bytes() != pages or GRID_CSV.read_bytes() != cells):
        raise SystemExit("Published transcription report or CSV differs from the audit")
    if args.write:
        REPORT.write_bytes(encoded)
        CSV.write_bytes(pages)
        GRID_CSV.write_bytes(cells)
    print("Verified 58 identical rune streams; 26 text variants, including 5 grid-cell disagreements")


if __name__ == "__main__":
    main()
