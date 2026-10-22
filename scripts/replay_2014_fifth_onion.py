"""Verify the preserved fifth-onion messages, audio, clues and square values."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-stage06"
REPORT = ROOT / "exports/cicada-2014-fifth-onion.json"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
AUDIO = ROOT / "exports/audio/interconnectedness.mp3"
REVISION = "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"
NAMES = {"README.md", "q4utgdi2n4m4uim5.asc", "q4utgdi2n4m4uim5.onion.asc",
         "magicsquares.txt", "01.hex", "02.hex", "03.hex", "01.jpg", "02.jpg",
         "03.mp3", "q4utgdi2n4m4uim5.onion.jpeg", "goya-peral-reference.jpg"}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def sources():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    if manifest["revision"] != REVISION:
        raise ValueError("Unexpected archive revision")
    files = {}
    for record in manifest["files"]:
        name = record["file"]
        if name not in NAMES:
            raise ValueError(f"Unexpected source: {name}")
        data = (SOURCE / name).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if (len(data), sha256(data), blob) != (record["bytes"], record["sha256"], record["git_blob_sha1"]):
            raise ValueError(f"Archived file changed: {name}")
        files[name] = data
    if set(files) != NAMES:
        raise ValueError("Source manifest incomplete")
    return manifest, files


def verified_messages(gpg):
    if not gpg or not Path(gpg).is_file():
        raise ValueError("GnuPG executable required; pass --gpg with its path")
    with tempfile.TemporaryDirectory(prefix="liberpedia-fifth-onion-") as scratch:
        base = [str(gpg), "--no-options", "--homedir", scratch, "--batch", "--no-tty"]
        imported = subprocess.run(base + ["--import", str(KEY)], capture_output=True)
        if imported.returncode:
            raise ValueError("Could not import the preserved Cicada key")
        messages = {}
        for name in ("q4utgdi2n4m4uim5.asc", "q4utgdi2n4m4uim5.onion.asc"):
            result = subprocess.run(base + ["--status-fd", "2", "--decrypt", str(SOURCE / name)], capture_output=True)
            if result.returncode or f"[GNUPG:] VALIDSIG {FINGERPRINT}".encode() not in result.stderr:
                raise ValueError(f"Signature verification failed: {name}")
            messages[name] = result.stdout
    return messages


def square_blocks(data):
    blocks = re.split(rb"\r?\n\s*\r?\n", data.strip())
    squares = []
    for block in blocks:
        rows = [[int(cell) for cell in line.split()] for line in block.splitlines()]
        size = len(rows)
        if size not in (5, 7) or any(len(row) != size for row in rows):
            raise ValueError("Unexpected square dimensions")
        sums = [sum(row) for row in rows]
        sums += [sum(row[column] for row in rows) for column in range(size)]
        sums += [sum(rows[i][i] for i in range(size)), sum(rows[i][size - 1 - i] for i in range(size))]
        if len(set(sums)) != 1:
            raise ValueError("Archived square is not magic")
        squares.append({"order": size, "line_sum": sums[0], "values": rows})
    if [(item["order"], item["line_sum"]) for item in squares] != [(5, 3301), (7, 1033), (5, 1033)]:
        raise ValueError("Unexpected archived squares")
    return squares


def replay(gpg):
    manifest, files = sources()
    signed = verified_messages(gpg)
    audio = bytes.fromhex(signed["q4utgdi2n4m4uim5.asc"].decode("ascii"))
    if not audio.startswith(b"ID3") or audio != AUDIO.read_bytes():
        raise ValueError("Signed hex does not reproduce the hosted MP3")
    nested = signed["q4utgdi2n4m4uim5.onion.asc"]
    previous = -1
    clues = []
    for number, extension, marker in (("01", "jpg", bytes([255, 216])),
                                      ("02", "jpg", bytes([255, 216])),
                                      ("03", "mp3", bytes([255, 243]))):
        hex_data = files[f"{number}.hex"]
        position = nested.find(hex_data)
        if position < 0 or position <= previous or nested.count(hex_data) != 1:
            raise ValueError(f"Hex clue is missing or out of order: {number}")
        previous = position
        decoded = bytes.fromhex(hex_data.decode("ascii"))
        if not decoded.startswith(marker) or decoded != files[f"{number}.{extension}"]:
            raise ValueError(f"Clue file differs from signed hex: {number}")
        clues.append({"number": number, "format": extension, "bytes": len(decoded),
                      "sha256": sha256(decoded), "signed_message_offset": position})
    coordinates = re.findall(rb"(?m)^(?:[A-Z0-9.\[\]]+:[0-9]+:[0-9]+:[0-9]+|[37]|ONION)$", nested)
    if len(coordinates) != 17 or coordinates[-1] != b"ONION":
        raise ValueError("Book-code pointers changed")
    squares = square_blocks(files["magicsquares.txt"])
    return {
        "schema": "liberpedia-2014-fifth-onion-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
        "signatures": {"fingerprint": FINGERPRINT, "two_clearsigned_messages_valid": True,
                       "key_trust": "Preserved public key; real-world identity not independently certified"},
        "interconnectedness_audio": {"bytes": len(audio), "sha256": sha256(audio), "format": "MP3 with ID3 header",
                                     "derived_from": "Hex in first verified clear-signed message"},
        "nested_clues": clues,
        "book_code_pointers": [item.decode("ascii") for item in coordinates],
        "archived_magic_squares": squares,
        "limits": [
            "The hosted magicsquares.txt matches the pinned archive, but this replay does not freshly extract it with OpenPuff.",
            "The book-code pointer list is authenticated by the saved signature; the Hofstadter text and each lookup are not independently replayed here.",
            "The portrait is an archived image; its proposed art attribution and interpretation are separate questions.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpg", type=Path, default=Path(shutil.which("gpg") or "gpg"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.check and args.write:
        parser.error("Choose --check or --write")
    report = replay(args.gpg)
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if args.check and REPORT.read_bytes() != encoded:
        raise SystemExit("Published report differs from replay")
    if args.write:
        REPORT.write_bytes(encoded)
    print("Verified two signatures, MP3, three signed clue files, pointer list and square sums")


if __name__ == "__main__":
    main()
