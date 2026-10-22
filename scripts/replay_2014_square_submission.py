"""Check the archived square-submission pages and signed follow-up message.

Run from any directory. Requires Pillow and GnuPG:
  python scripts/replay_2014_square_submission.py --check
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-square-submission"
REPORT = ROOT / "exports/cicada-2014-square-submission.json"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
REVISION = "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"
SOURCES = {
    "107.jpg", "167.jpg", "229.jpg",
    "009-squares-submission-pages--README.md",
    "010-hidden-service-reply--README.md", "message.txt.asc",
}
PAGE_MAP = {"107.jpg": "lp1-14", "167.jpg": "lp1-15", "229.jpg": "lp1-16"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def source_files():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest["revision"] != REVISION:
        raise ValueError("Unexpected source revision")
    files = {}
    for row in manifest["files"]:
        name = row["file"]
        if name not in SOURCES or name in files:
            raise ValueError(f"Unexpected or duplicate source: {name}")
        data = (SOURCE / name).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if (len(data), sha256(data), blob) != (row["bytes"], row["sha256"], row["git_blob_sha1"]):
            raise ValueError(f"Source differs from manifest: {name}")
        files[name] = data
    if set(files) != SOURCES:
        raise ValueError("Source manifest is incomplete")
    return manifest, files


def verify_message(gpg):
    if not gpg or not Path(gpg).is_file():
        raise ValueError("GnuPG executable required; pass --gpg with its path")
    with tempfile.TemporaryDirectory(prefix="liberpedia-square-reply-") as scratch:
        base = [str(gpg), "--no-options", "--homedir", scratch, "--batch", "--no-tty"]
        if subprocess.run(base + ["--import", str(KEY)], capture_output=True).returncode:
            raise ValueError("Could not import preserved public key")
        result = subprocess.run(base + ["--status-fd", "2", "--decrypt", str(SOURCE / "message.txt.asc")], capture_output=True)
    if result.returncode or f"[GNUPG:] VALIDSIG {FINGERPRINT}".encode() not in result.stderr:
        raise ValueError("Follow-up message signature failed")
    if b"ky2khlqdf7qdznac.onion" not in result.stdout:
        raise ValueError("Unexpected signed message content")
    return result.stdout


def replay(gpg):
    manifest, files = source_files()
    image_rows = []
    for name, page in PAGE_MAP.items():
        archived = files[name]
        hosted = (ROOT / "images" / f"{page}.jpg").read_bytes()
        with Image.open(BytesIO(archived)) as a, Image.open(BytesIO(hosted)) as b:
            a.load()
            b.load()
            if a.size[0] * 3 != a.size[1] * 2 or b.size != (2400, 3600):
                raise ValueError(f"Unexpected page dimensions: {name}")
            # The first archived copy is a distinct, smaller encoding. This
            # measurement describes it; it does not turn it into a byte match.
            average_difference = ImageStat.Stat(ImageChops.difference(
                a.convert("RGB"), b.convert("RGB").resize(a.size))).mean
            dimensions = list(a.size)
        exact = archived == hosted
        if (name != "107.jpg") != exact:
            raise ValueError(f"Unexpected exact image correspondence: {name}")
        image_rows.append({"archive_file": name, "page": page, "bytes": len(archived),
                           "sha256": sha256(archived), "dimensions": dimensions,
                           "hosted_image": f"images/{page}.jpg", "exact_hosted_match": exact,
                           "mean_rgb_difference_after_resize": [round(v, 3) for v in average_difference]})
    message = verify_message(gpg)
    return {
        "schema": "liberpedia-2014-square-submission-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
        "pages": image_rows,
        "follow_up": {"signed_text_sha256": sha256(message), "fingerprint": FINGERPRINT,
                      "valid_signature": True, "next_address": "ky2khlqdf7qdznac.onion",
                      "key_trust": "Preserved public key; real-world identity not independently certified"},
        "limits": [
            "The archive attributes the three pages to square submission; the surviving files alone do not establish the server-side submission transaction.",
            "107.jpg is a 1000x1500 archived copy of LP1-14, not an exact copy of the hosted 2400x3600 image.",
            "Signature verification checks the preserved message, not that a specific participant received it or that the hidden service remains available.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpg", type=Path, default=Path(shutil.which("gpg") or "gpg"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = (json.dumps(replay(args.gpg), indent=2) + "\n").encode("utf-8")
    if args.check and REPORT.read_bytes() != data:
        raise SystemExit("Published report differs from replay")
    if args.write:
        REPORT.write_bytes(data)
    print("Verified three archived page copies and the signed follow-up message")


if __name__ == "__main__":
    main()
