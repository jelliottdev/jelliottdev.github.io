"""Extract one documented OutGuess payload and compare its exact checksum.

Example: python scripts/extract_payload.py lp1-00 --outguess outguess --output cover.bin
Requires a locally installed OutGuess executable. Does not install software or
verify PGP signatures. Input images and extracted bytes are checked separately.
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", choices=["second-chance-2012", "opening-2014", "1033", "lp1-00", "lp1-01", "lp1-02", "lp1-03",
                                        "lp1-10", "lp1-11", "lp1-12", "lp1-13"])
    parser.add_argument("--outguess", default="outguess", help="Executable name or full path")
    parser.add_argument("--output", type=Path, required=True, help="New output file; never overwritten")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/evidence/embedded-payloads.json").read_text())
    if args.page == "second-chance-2012":
        record = json.loads((ROOT / "data/evidence/second-chance-2012.json").read_text())
    elif args.page == "opening-2014":
        record = json.loads((ROOT / "data/evidence/opening-2014.json").read_text())
    elif args.page == "1033":
        record = json.loads((ROOT / "data/evidence/illustrated-cover.json").read_text())["embedded_payload"]
    else:
        record = next(r for r in manifest["records"] if r["page"] == args.page)
    image = ROOT / f"images/{args.page}.jpg"
    sha = lambda data: hashlib.sha256(data).hexdigest()
    if sha(image.read_bytes()) != record["image_sha256"]:
        parser.error("Input JPEG differs from the pinned original. Download the original, not a thumbnail.")
    if args.output.exists():
        parser.error("Output already exists; choose a new filename.")
    with tempfile.TemporaryDirectory(prefix="liberpedia-outguess-") as directory:
        temporary = Path(directory) / "payload.bin"
        result = subprocess.run([args.outguess, "-r", "-k", "Default key", str(image), str(temporary)],
                                capture_output=True, timeout=20)
        if result.returncode or not temporary.exists():
            raise RuntimeError("Extraction failed: " + result.stderr.decode(errors="replace"))
        data = temporary.read_bytes()
        if sha(data) != record["payload_sha256"]:
            raise ValueError("Extraction returned different bytes. No verified output was saved.")
        with args.output.open("xb") as file:
            file.write(data)
    print(f"Verified {len(data)} bytes. SHA-256: {sha(data)}")
    print("This confirms extraction against the archived control; verify the signed message separately.")


if __name__ == "__main__":
    main()
