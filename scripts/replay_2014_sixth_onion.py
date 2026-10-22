"""Split the sixth-onion response into LP1-10–13 and verify its later signed form."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-sixth-onion"
REPORT = ROOT / "exports/cicada-2014-sixth-onion.json"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
REVISION = "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"
NAMES = {"README.md", "ut3qtzbrvs7dtvzp.onion.html", "ut3qtzbrvs7dtvzp.onion.headers",
         "ut3qtzbrvs7dtvzp.onion.v2-form.html", "ut3qtzbrvs7dtvzp.onion.v2-form.html.asc", "10-page.jpg"}
EXPECTED = {
    "lp1-10": (754662, "07910a858c17314c72c1af0fda25f8a04e5a700a71e25661111fc7bcf87e5210"),
    "lp1-11": (712733, "7bd11a2c9f5b512e33c9db170756e3b34cc1e29eb405373eb94957383a61be7d"),
    "lp1-12": (703428, "a5b58076e169f3f59c8a394dbef37da18226c9c4fff703df3be8dc95cf16291c"),
    "lp1-13": (2070134, "bef0fc4867c2363c835eb4f08029a1eba35c925e2f72659d7353cf8a91089e56"),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_sources():
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


def verify_form(files, gpg):
    signed = files["ut3qtzbrvs7dtvzp.onion.v2-form.html.asc"]
    if signed not in files["ut3qtzbrvs7dtvzp.onion.v2-form.html"]:
        raise ValueError("Saved HTML does not contain the signed form instruction")
    if not gpg or not Path(gpg).is_file():
        raise ValueError("GnuPG executable required; pass --gpg with its path")
    with tempfile.TemporaryDirectory(prefix="liberpedia-sixth-onion-") as scratch:
        base = [str(gpg), "--no-options", "--homedir", scratch, "--batch", "--no-tty"]
        imported = subprocess.run(base + ["--import", str(KEY)], capture_output=True)
        if imported.returncode:
            raise ValueError("Could not import the preserved Cicada key")
        result = subprocess.run(base + ["--status-fd", "2", "--decrypt",
                                        str(SOURCE / "ut3qtzbrvs7dtvzp.onion.v2-form.html.asc")], capture_output=True)
        if result.returncode or f"[GNUPG:] VALIDSIG {FINGERPRINT}".encode() not in result.stderr:
            raise ValueError("Later form instruction signature failed")
    if b"Please paste the magic squares" not in result.stdout or b"/cgi-bin/upload" not in result.stdout:
        raise ValueError("Unexpected signed instruction")
    return result.stdout


def take_jpeg(data):
    if not data.startswith(bytes([255, 216, 255])):
        raise ValueError("A page does not start with the JPEG marker")
    end = data.find(bytes([255, 217])) + 2
    if end < 3:
        raise ValueError("JPEG end marker missing")
    return data[:end], data[end:]


def replay(gpg):
    manifest, files = load_sources()
    source = files["ut3qtzbrvs7dtvzp.onion.html"]
    if not source.startswith(b"<!--761-->\n") or source.count(b"<body>") != 1:
        raise ValueError("Unexpected historical response framing")
    body = source.split(b"<body>", 1)[1].split(b"</body>", 1)[0]
    if not re.fullmatch(rb"[0-9a-fA-F\s]+", body):
        raise ValueError("Response body is not hexadecimal")
    stream = bytes.fromhex(body.decode("ascii"))
    if len(stream) != 4240957 or stream != (ROOT / "images/lp1-10.jpg").read_bytes():
        raise ValueError("The complete stream differs from the preserved LP1-10 carrier")
    remainder = stream
    outputs = {}
    for page in EXPECTED:
        jpeg, remainder = take_jpeg(remainder)
        expected_size, expected_hash = EXPECTED[page]
        if len(jpeg) != expected_size or sha256(jpeg) != expected_hash:
            raise ValueError(f"Unexpected page segment: {page}")
        comparison = SOURCE / "10-page.jpg" if page == "lp1-10" else ROOT / "images" / f"{page}.jpg"
        if jpeg != comparison.read_bytes():
            raise ValueError(f"Recovered page differs from hosted standalone JPEG: {page}")
        outputs[page] = jpeg
    if remainder:
        raise ValueError("Unaccounted bytes after four JPEGs")
    instruction = verify_form(files, gpg)
    report = {
        "schema": "liberpedia-2014-sixth-onion-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
        "response": {"marker": "<!--761-->", "hex_decoded_bytes": len(stream),
                     "sha256": sha256(stream), "matches_existing_lp1_10_carrier": True},
        "images": [{"page": page, "bytes": len(data), "sha256": sha256(data),
                    "standalone_path": "exports/sources/cicada-2014-sixth-onion/10-page.jpg" if page == "lp1-10" else f"images/{page}.jpg",
                    "matches_standalone": True}
                   for page, data in outputs.items()],
        "later_form": {"signed_instruction_sha256": sha256(instruction), "fingerprint": FINGERPRINT,
                       "valid_signature": True, "key_trust": "Preserved public key; real-world identity not independently certified"},
        "limits": [
            "The hosted images/lp1-10.jpg is the original 4,240,957-byte aggregate carrier, not a standalone first-page JPEG.",
            "The first JPEG segment is separately hosted as 10-page.jpg; the following three segments match images/lp1-11.jpg through lp1-13.jpg.",
            "The signed form proves what the preserved instruction says, not that anyone submitted squares or received a reply.",
        ],
    }
    return report, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpg", type=Path, default=Path(shutil.which("gpg") or "gpg"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--extract-dir", type=Path, help="Save four page-only JPEGs to a fresh destination")
    args = parser.parse_args()
    if args.check and args.write:
        parser.error("Choose --check or --write")
    report, outputs = replay(args.gpg)
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if args.check and REPORT.read_bytes() != encoded:
        raise SystemExit("Published report differs from replay")
    if args.write:
        REPORT.write_bytes(encoded)
    if args.extract_dir:
        targets = [args.extract_dir / f"{page}.jpg" for page in outputs]
        if any(path.exists() for path in targets):
            parser.error("A destination file already exists")
        args.extract_dir.mkdir(parents=True, exist_ok=True)
        for page, data in outputs.items():
            (args.extract_dir / f"{page}.jpg").write_bytes(data)
    print("Verified aggregate carrier, four page-only JPEGs and later signed form")


if __name__ == "__main__":
    main()
