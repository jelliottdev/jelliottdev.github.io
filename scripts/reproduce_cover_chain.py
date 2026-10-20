"""Reproduce the historical LP1-00 / LP1-01 / LP1-02 XOR and transposition.

Python 3, no dependencies. Checks every input and the reconstructed signed file.
This checks bytes; use GnuPG separately to verify the signature.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = [2, 8, 9, 1, 12, 13, 11, 4, 5, 7, 3, 0, 6, 10]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Save the reconstructed signed message; refuses overwriting")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "data/evidence/embedded-payloads.json").read_text())
    streams = []
    for page in manifest["cover_chain"]["pages"]:
        record = next(r for r in manifest["records"] if r["page"] == page)
        raw = (ROOT / record["body_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["body_sha256"]:
            raise ValueError(f"{page}: changed input body")
        streams.append(bytes.fromhex(raw.decode("ascii")))
    if len({len(s) for s in streams}) != 1:
        raise ValueError("The streams must have equal lengths; never pad or cycle them.")
    combined = bytes(a ^ b ^ c for a, b, c in zip(*streams))
    if hashlib.sha256(combined).hexdigest() != manifest["cover_chain"]["sha256"]:
        raise ValueError("Reconstructed message differs from the recorded bytes")
    if args.output:
        with args.output.open("xb") as file:
            file.write(combined)
    body = combined.split(b"\n\n", 1)[1].split(b"-----BEGIN PGP SIGNATURE-----")[0].strip()
    ciphertext = re.sub(rb"\s+", b"", body.split(b"Good luck.")[0]).decode("ascii")
    if len(ciphertext) != 70:
        raise ValueError("Expected 70 transposition characters")
    print(f"XOR: {len(combined)} bytes; SHA-256 {hashlib.sha256(combined).hexdigest()}")
    print("Five rows of fourteen characters, in source order:")
    for start in range(0, 70, 14):
        print(ciphertext[start:start+14])
    plaintext = "".join(ciphertext[start+column] for start in range(0, 70, 14) for column in COLUMNS)
    print("\nRead columns in this zero-based order:", COLUMNS)
    print(plaintext)
    print("\nThe literal output ends in ONIO. The historical .onion rendering restores a final N.")


if __name__ == "__main__":
    main()
