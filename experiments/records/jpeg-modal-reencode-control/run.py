"""Test whether the reported LP2 JPEG modal-byte class survives a fixed re-encode.

Requires Pillow 11.3.0 for exact reproduction. Original files are read only;
re-encoded bytes are held in memory and never offered as manuscript originals.
"""
from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path

from PIL import Image, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results.json"
QUALITIES = (75, 85, 95)


def modal_byte(data: bytes) -> tuple[int, int]:
    counts = Counter(data)
    maximum = max(counts.values())
    winners = [value for value in range(256) if counts[value] == maximum]
    if len(winners) != 1:
        raise ValueError(f"Tied modal bytes: {winners}")
    return winners[0], maximum


def run() -> dict:
    rows = []
    for number in range(58):
        name = f"lp2-{number:02d}"
        source = ROOT / "images" / f"{name}.jpg"
        original = source.read_bytes()
        original_mode, original_count = modal_byte(original)
        variants = {}
        for quality in QUALITIES:
            with Image.open(BytesIO(original)) as image:
                image.load()
                stream = BytesIO()
                image.save(stream, format="JPEG", quality=quality, subsampling=0)
            encoded = stream.getvalue()
            mode, count = modal_byte(encoded)
            variants[str(quality)] = {
                "modal_byte_hex": f"{mode:02X}", "modal_count": count,
                "file_bytes": len(encoded), "sha256": sha256(encoded).hexdigest(),
            }
        rows.append({
            "page": name, "original_sha256": sha256(original).hexdigest(),
            "original_modal_byte_hex": f"{original_mode:02X}",
            "original_modal_count": original_count,
            "original_file_bytes": len(original), "reencoded": variants,
        })
    counts = {"original": sum(r["original_modal_byte_hex"] != "00" for r in rows)}
    for quality in QUALITIES:
        counts[str(quality)] = sum(r["reencoded"][str(quality)]["modal_byte_hex"] != "00" for r in rows)
    four = [r["page"] for r in rows if r["original_modal_byte_hex"] != "00"]
    assert four == ["lp2-00", "lp2-04", "lp2-24", "lp2-26"]
    return {
        "schema": "liberpedia-jpeg-modal-reencode-v1",
        "pillow_version": pillow_version,
        "rule": "Pillow JPEG decode, then JPEG encode quality 75/85/95 with subsampling=0; retain decoded image mode; count all encoded bytes 00-FF",
        "summary": {"nonzero_modal_page_counts": counts, "original_four_pages": four},
        "files": rows,
        "limits": "Re-encoded JPEGs change pixels and file bytes; this is a representation-sensitivity control, not a hidden-message extraction or original-file replacement.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the saved report")
    parser.add_argument("--write", action="store_true", help="Write the report (author use)")
    args = parser.parse_args()
    result = run()
    if args.check:
        assert result == json.loads(OUT.read_text(encoding="utf-8")), "saved report differs"
        print("PASS: 58 originals and 174 fixed re-encodes reproduce the report")
    elif args.write:
        OUT.write_bytes((json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    else:
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
