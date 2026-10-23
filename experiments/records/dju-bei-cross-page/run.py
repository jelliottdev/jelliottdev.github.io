"""Locate the repeated DJU-BEI rune sequence on LP2-27 and LP2-55."""

import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUTPUT = HERE / "results.json"
RUNES = set("ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ")
TARGET = "ᛞᛄᚢᛒᛖᛁ"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def page(number):
    path = ROOT / f"data/pages/lp2-{number:02}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data["raw"]
    positions = []
    line_number = column_number = 1
    for offset, char in enumerate(raw):
        if char in RUNES:
            positions.append((offset, line_number, column_number))
        if char == "\n":
            line_number += 1
            column_number = 1
        else:
            column_number += 1
    filtered = "".join(raw[offset] for offset, _, _ in positions)
    assert len(filtered) == data["rune_count"], (number, len(filtered), data["rune_count"])
    occurrences = []
    for start in range(len(filtered) - len(TARGET) + 1):
        if filtered[start:start + len(TARGET)] != TARGET:
            continue
        a = positions[start]
        b = positions[start + len(TARGET) - 1]
        occurrences.append({
            "zero_based_rune_offset": start,
            "one_based_rune_position": start + 1,
            "source_line_start": a[1],
            "source_column_start": a[2],
            "source_line_end": b[1],
            "source_column_end": b[2],
            "source_slice": raw[a[0]:b[0] + 1],
        })
    return {"page": data["id"], "source": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": digest(path), "rune_count": len(filtered),
            "occurrences": occurrences}


def report():
    pages = [page(27), page(55)]
    assert [row["rune_count"] for row in pages] == [234, 76]
    assert [[o["zero_based_rune_offset"] for o in row["occurrences"]] for row in pages] == [[28], [70]]
    assert [row["occurrences"][0]["source_slice"] for row in pages] == ["ᛞᛄᚢ-ᛒᛖᛁ"] * 2
    return {
        "schema": "liberpedia-dju-bei-cross-page-v1",
        "target_runes": TARGET,
        "transliteration": "DJU-BEI",
        "rule": "Scan each page independently; keep only the 29 GP runes, including headings, in printed order. Punctuation, spaces, hyphens, slashes and line breaks do not advance the rune offset. No window crosses a page boundary.",
        "pages": pages,
        "limits": [
            "This checks two specified archived page transcriptions, not all LP2 pages or an image-level transcription audit.",
            "The match was known before the audit; its frequency is descriptive, not a surprise probability.",
            "The shared six runes do not identify a cipher, key, copying mechanism or relation to doublet suppression."
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    content = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        assert OUTPUT.read_bytes() == content, "results.json differs from replay"
    else:
        OUTPUT.write_bytes(content)
    print("DJU-BEI offsets:", [(p["page"], p["occurrences"][0]["zero_based_rune_offset"])
                               for p in result["pages"]])


if __name__ == "__main__":
    main()
