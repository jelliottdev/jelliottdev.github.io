"""Recover the first three LP1 JPEGs from the archived 2014 server response."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-stage03"
REPORT = ROOT / "exports/cicada-2014-response.json"
IMAGES = [
    ("lp1-00", 168876, "184e6f9de8695d99435c2bef4fd7e304a8a0f704dbe04439fa8bf13c4da395a7"),
    ("lp1-01", 1476614, "71f4bd03c692ede630091272597d2b18702184ed32fdd1977ef0ba7306632b46"),
    ("lp1-02", 175159, "0297572bbc2d234f84df634c6f0474011ff5df66c2ce987c3bb7aa0c635799b4"),
]


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_sources():
    manifest_raw = (SOURCE / "manifest.json").read_bytes()
    manifest = json.loads(manifest_raw)
    if manifest["revision"] != "10733feb487bb8beb9966d534727ee5897aa54fc":
        raise ValueError("Unexpected archive revision")
    files = {}
    for record in manifest["files"]:
        name = record["file"]
        if name not in {"README.md", "index.html", "index.html.2"}:
            raise ValueError(f"Unexpected source: {name}")
        raw = (SOURCE / name).read_bytes()
        git_blob = hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()
        if len(raw) != record["bytes"] or sha256(raw) != record["sha256"] or git_blob != record["git_blob_sha1"]:
            raise ValueError(f"Archived source bytes changed: {name}")
        files[name] = raw
    if set(files) != {"README.md", "index.html", "index.html.2"}:
        raise ValueError("Source manifest is incomplete")
    return manifest, files


def parse_response(raw, marker):
    lines = raw.splitlines()
    if len(lines) != 2 or lines[0] != marker:
        raise ValueError("Unexpected response framing")
    try:
        return bytes.fromhex(lines[1].decode("ascii"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError("Response body is not complete hexadecimal data") from error


def reconstruct():
    manifest, files = verify_sources()
    initial = parse_response(files["index.html"], b"<!--Patience is a virtue-->")
    full = parse_response(files["index.html.2"], b"<!--761-->")
    if len(initial) != 256 or len(full) != sum(size for _, size, _ in IMAGES):
        raise ValueError("Unexpected decoded response lengths")
    inverted = bytes(byte ^ 0xFF for byte in full)
    outputs = {}
    position = 0
    for index, (page, length, expected_hash) in enumerate(IMAGES):
        part = inverted[position:position + length]
        position += length
        if index == 2:
            part = part[::-1]
        existing = (ROOT / "images" / f"{page}.jpg").read_bytes()
        if sha256(part) != expected_hash or part != existing:
            raise ValueError(f"Reconstructed JPEG differs from preserved {page}")
        outputs[page] = part
    if position != len(inverted):
        raise ValueError("Unconsumed response bytes")

    report = {
        "schema": "liberpedia-2014-response-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(raw), "sha256": sha256(raw)} for name, raw in files.items()},
        "initial_response": {"marker": "<!--Patience is a virtue-->", "hex_decoded_bytes": len(initial),
                             "prefix_of_complete_response": full.startswith(initial)},
        "complete_response": {"marker": "<!--761-->", "hex_decoded_bytes": len(full),
                              "operation": "XOR each decoded byte with 0xFF, split at fixed byte offsets, then reverse the third segment"},
        "images": [{"page": page, "offset_in_inverted_stream": sum(item[1] for item in IMAGES[:index]),
                    "bytes": len(outputs[page]), "reverse_segment": index == 2,
                    "sha256": sha256(outputs[page]), "matches_hosted_original": True}
                   for index, (page, _, _) in enumerate(IMAGES)],
        "next_step": "The existing cover-chain replay extracts signed hex streams from these three JPEGs, XORs them and reorders a 5-by-14 ciphertext matrix.",
        "limits": [
            "These are archived response captures, not a live request to the historical service.",
            "The short initial capture is not a byte prefix of the complete response; this replay does not infer the server's update schedule.",
            "Matching JPEG bytes does not itself verify their embedded signatures or solve the later transposition; those checks are documented separately.",
        ],
    }
    return report, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the reconstructed report with the published JSON")
    parser.add_argument("--write", action="store_true", help="Regenerate the published JSON report")
    parser.add_argument("--extract-dir", type=Path, help="Save the three verified JPEGs here; refuse to overwrite files")
    args = parser.parse_args()
    if args.check and args.write:
        parser.error("Choose --check or --write, not both")
    report, outputs = reconstruct()
    encoded = (json.dumps(report, indent=2) + "\n").encode("utf-8")
    if args.check:
        if REPORT.read_bytes() != encoded:
            raise SystemExit("Published response report differs from the replay")
    if args.write:
        REPORT.write_bytes(encoded)
    if args.extract_dir:
        targets = [args.extract_dir / f"{page}.jpg" for page in outputs]
        if any(target.exists() for target in targets):
            parser.error("A target JPEG already exists; nothing was overwritten")
        args.extract_dir.mkdir(parents=True, exist_ok=True)
        for page, target in zip(outputs, targets):
            target.write_bytes(outputs[page])
    print("PASS: archived response yields LP1-00, LP1-01 and LP1-02 byte for byte")


if __name__ == "__main__":
    main()
