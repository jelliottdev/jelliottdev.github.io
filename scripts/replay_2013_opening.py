"""Check the preserved 2013 opening JPEG, extracted book code and signature."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "exports/sources/cicada-2013/232.jpg"
PAYLOAD = ROOT / "exports/sources/cicada-2013/232.jpg.asc"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
OUTPUT = ROOT / "exports/cicada-2013-opening.json"
EXPECTED = {
    "image": "6e95b0011a9103dc97cc453d094b7815ce900e83e910f29e1f7a0ef822d2b67b",
    "payload": "0dc4218d36e5bdfc453d7955b3297e4efdc518b2d15fa2df65fbb0476618659a",
    "key": "1e1992b73916c356ffda19c3c1cbdfb206e6318910b0f502aa1e6e49a1fa41c7",
}
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"
SOURCE = "https://raw.githubusercontent.com/neuroretransmit/cicada/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2013/001-232.jpg/232.jpg"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command):
    return subprocess.run(command, capture_output=True, text=True, errors="replace", timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outguess", type=Path, help="Run a fresh extraction from the saved JPEG")
    parser.add_argument("--gpg", type=Path, help="Verify the payload against an isolated copy of the saved key")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    paths = {"image": IMAGE, "payload": PAYLOAD, "key": KEY}
    data = {name: path.read_bytes() for name, path in paths.items()}
    hashes = {name: digest(contents) for name, contents in data.items()}
    if hashes != EXPECTED:
        raise SystemExit(f"Saved input hash mismatch: {hashes}")
    signed = data["payload"].decode("ascii")
    if "Welcome again." not in signed or "A book whose study is forbidden" not in signed:
        raise SystemExit("Expected riddle is missing")
    body = signed.split("-----BEGIN PGP SIGNATURE-----", 1)[0]
    coordinates = re.findall(r"^(?:I|II|III):\d+:\d+$", body, flags=re.MULTILINE)
    literals = re.findall(r"^\d+$", body, flags=re.MULTILINE)
    if len(coordinates) != 44 or literals != ["5", "0", "3301"]:
        raise SystemExit("The book-code coordinate or literal count changed")

    report = {
        "source_image_url": SOURCE,
        "source_revision": "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3",
        "files": {name: {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data[name]),
                         "sha256": hashes[name]} for name, path in paths.items()},
        "book_code": {"coordinate_count": len(coordinates), "literal_digits_between_coordinates": ["5", "0"],
                      "sign_off_below_coordinates": "3301"},
        "outguess_run": None,
        "gpg_run": None,
        "limits": [
            "The preserved JPEG is from a pinned artifact archive; its original 4chan upload time is not verified here.",
            "A valid signature binds the payload to the preserved key, not independently to a real-world identity.",
            "The coordinate count does not itself establish the book or perform the book-code lookup.",
        ],
    }

    with tempfile.TemporaryDirectory(prefix="liberpedia-2013-opening-") as scratch_dir:
        scratch = Path(scratch_dir)
        verified_payload = PAYLOAD
        if args.outguess:
            if not args.outguess.is_file():
                parser.error("OutGuess executable not found")
            fresh = scratch / "232.jpg.asc"
            result = run([str(args.outguess.resolve()), "-r", str(IMAGE), str(fresh)])
            fresh_bytes = fresh.read_bytes() if fresh.exists() else b""
            matched = result.returncode == 0 and fresh_bytes == data["payload"]
            report["outguess_run"] = {
                "executable_sha256": digest(args.outguess.read_bytes()),
                "exit_code": result.returncode,
                "diagnostic": (result.stdout + result.stderr).replace(str(IMAGE), "232.jpg").strip(),
                "extracted_bytes": len(fresh_bytes),
                "matches_saved_payload": matched,
            }
            if not matched:
                raise SystemExit("Fresh OutGuess extraction did not match the saved payload")
            verified_payload = fresh
        if args.gpg:
            if not args.gpg.is_file():
                parser.error("GPG executable not found")
            homedir = scratch / "gnupg"
            homedir.mkdir()
            prefix = [str(args.gpg.resolve()), "--homedir", str(homedir), "--batch", "--no-tty"]
            if run(prefix + ["--import", str(KEY)]).returncode:
                raise SystemExit("Could not import the preserved public key")
            result = run(prefix + ["--status-fd", "1", "--verify", str(verified_payload)])
            status = result.stdout + result.stderr
            valid = result.returncode == 0 and f"[GNUPG:] VALIDSIG {FINGERPRINT}" in status
            report["gpg_run"] = {"exit_code": result.returncode, "fingerprint": FINGERPRINT,
                                 "valid_signature": valid, "key_trust": "not independently certified"}
            if not valid:
                raise SystemExit("Signature did not verify with the preserved public key")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Saved inputs checked; OutGuess: {report['outguess_run'] is not None}; GPG: {report['gpg_run'] is not None}")


if __name__ == "__main__":
    main()
