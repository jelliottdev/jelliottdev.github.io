"""Check the surviving 2012 closing JPEG, its OutGuess payload and signature."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
IMAGE = ROOT / "exports/sources/cicada-2012-ending/valete.jpg"
PAYLOAD = ROOT / "exports/sources/cicada-2012-ending/valete.asc"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
OUTPUT = ROOT / "exports/cicada-2012-valete.json"
EXPECTED = {
    "image": "6c8a8e3096208718d75a59d62ac5f66428e73b64e8bb3bdf689ff5dddee84ce4",
    "payload": "db68f6e38d5f8eab3f13cd3296465a5b562c84d581cc1121dda6ef9da9a8cb6b",
    "key": "1e1992b73916c356ffda19c3c1cbdfb206e6318910b0f502aa1e6e49a1fa41c7",
}
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(args, timeout=20):
    return subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outguess", type=Path, help="Run this executable against the saved JPEG")
    parser.add_argument("--gpg", type=Path, help="Verify the signed payload in an isolated keyring")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    data = {"image": IMAGE.read_bytes(), "payload": PAYLOAD.read_bytes(), "key": KEY.read_bytes()}
    hashes = {name: digest(value) for name, value in data.items()}
    if hashes != EXPECTED:
        raise SystemExit(f"Saved input hash mismatch: {hashes}")
    text = data["payload"].decode("ascii")
    if "We have now found the individuals we sought." not in text:
        raise SystemExit("Expected closing text is missing")
    postscript = text.split("P.S. ", 1)[1].split("-----BEGIN PGP SIGNATURE-----", 1)[0]
    digits = "".join(re.findall(r"[0-9]+", postscript))
    if len(digits) != 131:
        raise SystemExit("Postscript digit count changed")

    report = {
        "reddit_post": "https://www.reddit.com/r/a2e7j6ic78h0j/comments/pdtbj/val%C4%93te/",
        "reddit_created_utc": "2012-02-06T23:27:05Z",
        "image_url_in_post": "http://i.imgur.com/vjuNp.jpg",
        "files": {name: {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data[name]), "sha256": hashes[name]}
                  for name, path in [("image", IMAGE), ("payload", PAYLOAD), ("key", KEY)]},
        "postscript_digits": len(digits),
        "postscript": digits,
        "outguess_run": None,
        "gpg_run": None,
        "limits": [
            "The Reddit timestamp and image URL are recorded from the surviving post; this script does not query Reddit.",
            "A valid signature proves that the extracted bytes match the preserved public key; it does not independently establish the real-world identity of the key holder.",
            "The 131-digit postscript is recorded without a decoding claim.",
        ],
    }
    with tempfile.TemporaryDirectory(prefix="liberpedia-valete-") as scratch:
        scratch = Path(scratch)
        verified_payload = PAYLOAD
        if args.outguess:
            if not args.outguess.is_file():
                parser.error("OutGuess executable not found")
            fresh = scratch / "valete.asc"
            result = run([str(args.outguess.resolve()), "-r", str(IMAGE), str(fresh)])
            fresh_bytes = fresh.read_bytes() if fresh.exists() else b""
            matched = result.returncode == 0 and fresh_bytes == data["payload"]
            diagnostic = (result.stdout + result.stderr).replace(str(IMAGE), "valete.jpg").strip()
            report["outguess_run"] = {
                "executable_sha256": digest(args.outguess.read_bytes()),
                "exit_code": result.returncode,
                "diagnostic": diagnostic,
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
            base = [str(args.gpg.resolve()), "--homedir", str(homedir), "--batch", "--no-tty"]
            imported = run(base + ["--import", str(KEY)])
            if imported.returncode:
                raise SystemExit("Could not import the preserved public key")
            result = run(base + ["--status-fd", "1", "--verify", str(verified_payload)])
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
