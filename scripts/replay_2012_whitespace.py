"""Replay the preserved 2012 website's tab/space message without BeautifulSoup."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/whitespace-2012"
KEY = ROOT / "exports/steganography/cicada-public-key.asc"
FINGERPRINT = "6D854CD7933322A601C3286D181F01E57A35090F"


class PreText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.depth += 1
            self.blocks.append([])

    def handle_endtag(self, tag):
        if tag == "pre":
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.blocks[-1].append(data)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replay():
    manifest = json.loads((SOURCE / "manifest.json").read_text(encoding="utf-8"))
    for item in manifest["sources"]:
        path = SOURCE / item["file"]
        if sha(path.read_bytes()) != item["sha256"]:
            raise ValueError("Source changed: " + item["file"])
    html = (SOURCE / "whitespace.html").read_text(encoding="utf-8")
    parser = PreText()
    parser.feed(html)
    if len(parser.blocks) != 1:
        raise ValueError("Expected exactly one preformatted block")
    text = "".join(parser.blocks[0])
    if set(text) - {" ", "\t", "\n"}:
        raise ValueError("Unexpected character inside the binary block")
    rows = text.split("\n")
    encoded = []
    for number, row in enumerate(rows, 1):
        bits = "".join("1" if c == " " else "0" for c in row)
        if len(bits) % 8:
            raise ValueError(f"Row {number} does not contain whole bytes")
        encoded.append(bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)))
    decoded = b"\n".join(encoded)
    archived = (SOURCE / "whitespace.asc").read_bytes()
    if decoded != archived:
        raise ValueError("Fresh whitespace decoding differs from archived signed text")
    lines = decoded.decode("ascii").splitlines()
    image_numbers = [line.strip() for line in lines if re.fullmatch(r"[0-9]{12}\s*", line)]
    if len(image_numbers) != 10 or len(set(image_numbers)) != 10:
        raise ValueError("Expected ten distinct twelve-digit image numbers")
    return {
        "schema": "liberpedia-2012-whitespace-v1",
        "source_revision": manifest["revision"],
        "html_sha256": sha((SOURCE / "whitespace.html").read_bytes()),
        "archived_message_sha256": sha(archived),
        "decoded_message_sha256": sha(decoded),
        "decoded_matches_archive": True,
        "pre_blocks": len(parser.blocks),
        "encoded_rows": len(rows),
        "space_bits": text.count(" "),
        "tab_bits": text.count("\t"),
        "total_bits": text.count(" ") + text.count("\t"),
        "decoded_bytes": len(decoded),
        "bit_rule": "space=1, tab=0; eight bits per byte; newline ends an encoded line",
        "message_lines": len(lines),
        "image_numbers": image_numbers,
        "signature_marker": "-----BEGIN PGP SIGNED MESSAGE-----" in lines,
        "declared_hash": next((line for line in lines if line.startswith("Hash: ")), None),
    }


def verify_with_gpg(executable):
    with tempfile.TemporaryDirectory(prefix="liberpedia-2012-whitespace-") as folder:
        home = Path(folder) / "gnupg"
        home.mkdir()
        base = [str(executable.resolve()), "--homedir", str(home), "--batch", "--no-tty"]
        imported = subprocess.run(base + ["--import", str(KEY)], capture_output=True, text=True)
        if imported.returncode:
            raise ValueError("Could not import the preserved public key")
        checked = subprocess.run(base + ["--status-fd", "1", "--verify", str(SOURCE / "whitespace.asc")],
                                 capture_output=True, text=True)
        status = checked.stdout + checked.stderr
        valid = checked.returncode == 0 and f"[GNUPG:] VALIDSIG {FINGERPRINT}" in status
        if not valid:
            raise ValueError("The signed message did not verify with the preserved key")
        return {"valid_signature": True, "key_fingerprint": FINGERPRINT,
                "gpg_version": subprocess.run([str(executable.resolve()), "--version"],
                                              capture_output=True, text=True).stdout.splitlines()[0],
                "identity_trust": "public key identity not independently certified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--output", type=Path)
    parser.add_argument("--gpg", type=Path, help="Optional GnuPG executable for fresh signature verification")
    args = parser.parse_args()
    report = replay()
    if args.check:
        saved = json.loads((ROOT / "exports/cicada-2012-whitespace.json").read_text(encoding="utf-8"))
        if report != saved:
            raise SystemExit("Replay differs from the saved report")
    if args.gpg:
        report["gpg_run"] = verify_with_gpg(args.gpg)
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    print(f"Decoded {report['decoded_bytes']} bytes, {len(report['image_numbers'])} image numbers; "
          f"archive match: {report['decoded_matches_archive']}; GPG: {bool(args.gpg)}")


if __name__ == "__main__":
    main()
