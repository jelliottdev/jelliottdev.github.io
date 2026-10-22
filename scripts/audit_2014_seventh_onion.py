"""Compare all 58 archived seventh-onion JPEGs with Liberpedia's LP2 page JPEGs.

Run from any directory. Requires Pillow:
  python scripts/audit_2014_seventh_onion.py --check
"""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-seventh-onion"
REPORT = ROOT / "exports/cicada-2014-seventh-onion.json"
CSV = ROOT / "exports/cicada-2014-seventh-onion-pages.csv"
REVISION = "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
ARCHIVE_FILES = {"README.md", "ky2khlqdf7qdznac.onion.html"} | {f"{i}.jpg" for i in range(58)}
JFIF = b"\xff\xe0\x00\x10JFIF\x00"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest["revision"] != REVISION:
        raise ValueError("Unexpected archive revision")
    files = {}
    for row in manifest["files"]:
        name = row["file"]
        if name not in ARCHIVE_FILES or name in files:
            raise ValueError(f"Unexpected or duplicate archived file: {name}")
        data = (SOURCE / name).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if (len(data), sha256(data), blob) != (row["bytes"], row["sha256"], row["git_blob_sha1"]):
            raise ValueError(f"Archived file differs from pinned manifest: {name}")
        files[name] = data
    if set(files) != ARCHIVE_FILES:
        raise ValueError("The preserved source set is incomplete")
    listed = [int(x) for x in re.findall(rb'<img src="([0-9]+)\.jpg"', files["ky2khlqdf7qdznac.onion.html"])]
    if listed != list(range(58)):
        raise ValueError("The saved HTML does not list pages 0 through 57 in order")
    return manifest, files


def audit():
    manifest, files = sources()
    pages = []
    for number in range(58):
        page = f"lp2-{number:02}"
        archive = files[f"{number}.jpg"]
        hosted = (ROOT / "images" / f"{page}.jpg").read_bytes()
        record = json.loads((ROOT / "data/pages" / f"{page}.json").read_text(encoding="utf-8"))
        if sha256(hosted) != record["image_sha256"]:
            raise ValueError(f"Hosted page differs from its page record: {page}")
        if hosted == archive:
            relation = "byte-identical"
        elif hosted[:2] + hosted[20:] == archive and hosted[2:11] == JFIF:
            relation = "hosted-adds-18-byte-JFIF"
        else:
            relation = "different-JPEG-image-data"
        with Image.open(io.BytesIO(archive)) as a, Image.open(io.BytesIO(hosted)) as b:
            a.load()
            b.load()
            if a.size != (2400, 3600) or b.size != a.size:
                raise ValueError(f"Unexpected image dimensions: {page}")
            difference = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
            pixel_identical = difference.getbbox() is None
            mean = round(sum(ImageStat.Stat(difference).mean) / 3, 6)
        if relation == "hosted-adds-18-byte-JFIF" and not pixel_identical:
            raise ValueError(f"A header-only difference changed pixels: {page}")
        pages.append({
            "page": page, "archived_file": f"{number}.jpg",
            "archived_path": f"exports/sources/cicada-2014-seventh-onion/{number}.jpg",
            "archived_bytes": len(archive), "archived_sha256": sha256(archive),
            "hosted_path": f"images/{page}.jpg", "hosted_bytes": len(hosted),
            "hosted_sha256": sha256(hosted), "byte_difference": len(hosted) - len(archive),
            "relationship": relation, "decoded_pixels_identical": pixel_identical,
            "mean_absolute_rgb_difference": mean,
        })
    counts = Counter(p["relationship"] for p in pages)
    if counts != {"hosted-adds-18-byte-JFIF": 35, "different-JPEG-image-data": 23}:
        raise ValueError(f"Unexpected relationship counts: {counts}")
    if any(p["decoded_pixels_identical"] for p in pages if p["relationship"] == "different-JPEG-image-data"):
        raise ValueError("Expected the 23 separately encoded pages to have small pixel differences")
    report = {
        "schema": "liberpedia-2014-seventh-onion-audit-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "saved_html_images": 58,
        "counts": dict(counts),
        "pages": pages,
        "limits": [
            "The preserved repository files and Liberpedia's three-mirror page files are two distinct source sets. Neither set is independently authenticated as the creator's original 2014 bytes.",
            "The 35 header-only cases are pixel-identical, but a byte-level or steganographic analysis must use the declared version.",
            "The other 23 images differ in JPEG data and slightly in decoded pixels. This audit does not establish why they were encoded differently or which version is historically earlier.",
            "The saved seventh-onion HTML lists 0.jpg through 57.jpg; it does not authenticate a live onion service today.",
        ],
    }
    return report


def csv_text(report):
    fields = ["page", "archived_file", "archived_path", "archived_bytes", "archived_sha256",
              "hosted_path", "hosted_bytes", "hosted_sha256", "byte_difference",
              "relationship", "decoded_pixels_identical", "mean_absolute_rgb_difference"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(report["pages"])
    return output.getvalue().encode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = audit()
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    table = csv_text(report)
    if args.check and (REPORT.read_bytes() != encoded or CSV.read_bytes() != table):
        raise SystemExit("Published report or CSV differs from the audit")
    if args.write:
        REPORT.write_bytes(encoded)
        CSV.write_bytes(table)
    print("Verified 58 archived LP2 JPEGs: 35 header-only differences, 23 different image streams")


if __name__ == "__main__":
    main()
