"""Check two archived 2012 subreddit image payloads and their signatures."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2012-subreddit"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"
SOURCES = {
    "KXLOP.jpg": "7bc12b2647b38cb426ffb54f9369f36526a1360f53f859c26e41cb7e92565ea6",
    "KXLOP.jpg.asc": "ce6c44a4c3daf6d5b3691f8894ddb59b10ab58514ce1a2e692caf9b86af7142a",
    "8D7hN.jpg": "2d9e10b6d779ebc5664bbe21f575e4bb52f58d50ce39b0c1c0d17e741dc52f80",
    "8D7hN.jpg.asc": "f7d8e962db5f34a3e2300312c5ed150216974cae3b398fbc867b9dae727e1dab",
    "UMa-nedknxEIvArh.png": "29ca61a2fc21e7a4af2a217b13e4092cc6abf18b66edc5aa56fdb71e65885846",
}
IMAGE_PAIRS = (("KXLOP.jpg", "KXLOP.jpg.asc"), ("8D7hN.jpg", "8D7hN.jpg.asc"))
ARCHIVE = "https://raw.githubusercontent.com/neuroretransmit/cicada/ade9a02889ef8acbc8cde8edbfd0a785c369f4c3/2012/003-subreddit/"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def command(argv):
    return subprocess.run(argv, capture_output=True, text=True, errors="replace", timeout=30)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outguess", type=Path, help="Executable for a fresh extraction")
    parser.add_argument("--gpg", type=Path, help="Executable for an isolated signature check")
    parser.add_argument("--output", type=Path, default=ROOT / "exports/cicada-2012-subreddit-images.json")
    args = parser.parse_args()

    files = {}
    for name, expected in SOURCES.items():
        data = (SOURCE / name).read_bytes()
        if digest(data) != expected:
            raise SystemExit(f"Source hash changed: {name}")
        files[name] = {"bytes": len(data), "sha256": expected}
    welcome = (SOURCE / "KXLOP.jpg.asc").read_text(encoding="ascii")
    problems = (SOURCE / "8D7hN.jpg.asc").read_text(encoding="ascii")
    if "Key ID 7A35090F" not in welcome or "Patience is a virtue." not in welcome:
        raise SystemExit("Welcome payload wording changed")
    if "The key has always been right in front of your eyes." not in problems:
        raise SystemExit("Problems payload wording changed")

    report = {
        "source_revision": "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3",
        "source_urls": {
            "KXLOP.jpg": ARCHIVE + "posts/KXLOP.jpg",
            "KXLOP.jpg.asc": ARCHIVE + "posts/KXLOP.jpg.asc",
            "8D7hN.jpg": ARCHIVE + "posts/8D7hN.jpg",
            "8D7hN.jpg.asc": ARCHIVE + "posts/8D7hN.jpg.asc",
            "UMa-nedknxEIvArh.png": ARCHIVE + "banner/UMa-nedknxEIvArh.png",
        },
        "files": files,
        "payload_observations": {
            "welcome_mentions_key_id": "7A35090F",
            "problems_hint": "The key has always been right in front of your eyes.",
            "banner_maya_values_from_visual_inspection": [10, 2, 14, 7, 19, 6, 18, 12, 7, 8, 17, 0, 19],
            "key_prefix_from_subreddit_info": [int(c, 36) for c in "a2e7j6ic78h0j"],
        },
        "outguess_run": None,
        "gpg_run": None,
        "limits": [
            "Pinned archive bytes and archived Reddit metadata do not prove an original posting time or uploader identity.",
            "The banner displays only the first thirteen values of the longer key in the subreddit-info string.",
            "A valid signature binds a payload to the preserved public key, not to an independently certified person.",
        ],
    }
    assert report["payload_observations"]["banner_maya_values_from_visual_inspection"] == report["payload_observations"]["key_prefix_from_subreddit_info"]

    if args.outguess and not args.outguess.is_file():
        parser.error("OutGuess executable not found")
    if args.gpg and not args.gpg.is_file():
        parser.error("GPG executable not found")
    with tempfile.TemporaryDirectory(prefix="liberpedia-subreddit-") as folder:
        scratch = Path(folder)
        if args.outguess:
            outguess_run = {}
            for image, payload in IMAGE_PAIRS:
                fresh = scratch / payload
                result = command([str(args.outguess.resolve()), "-r", str(SOURCE / image), str(fresh)])
                data = fresh.read_bytes() if fresh.exists() else b""
                matches = result.returncode == 0 and data == (SOURCE / payload).read_bytes()
                outguess_run[image] = {
                    "exit_code": result.returncode,
                    "extracted_bytes": len(data),
                    "matches_archived_payload": matches,
                    "diagnostic": (result.stdout + result.stderr).replace(str(SOURCE), "<source>").strip(),
                }
                if not matches:
                    raise SystemExit(f"Fresh extraction mismatch: {image}")
            report["outguess_run"] = {"executable_sha256": digest(args.outguess.read_bytes()), "images": outguess_run}
        if args.gpg:
            homedir = scratch / "gnupg"
            homedir.mkdir()
            base = [str(args.gpg.resolve()), "--homedir", str(homedir), "--batch", "--no-tty"]
            if command(base + ["--import", str(KEY)]).returncode:
                raise SystemExit("Could not import preserved public key")
            gpg_run = {}
            for _, payload in IMAGE_PAIRS:
                result = command(base + ["--status-fd", "1", "--verify", str(SOURCE / payload)])
                status = result.stdout + result.stderr
                valid = result.returncode == 0 and f"[GNUPG:] VALIDSIG {FINGERPRINT}" in status
                gpg_run[payload] = {"exit_code": result.returncode, "valid_signature": valid}
                if not valid:
                    raise SystemExit(f"Signature failed: {payload}")
            report["gpg_run"] = {"fingerprint": FINGERPRINT, "key_trust": "not independently certified", "payloads": gpg_run}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("Two archived payloads checked; OutGuess:", bool(args.outguess), "GPG:", bool(args.gpg))


if __name__ == "__main__":
    main()
