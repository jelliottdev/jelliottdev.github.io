"""Recover LP1-06–09 from the archived fourth-onion gzip response."""

import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-stage05"
REPORT = ROOT / "exports/cicada-2014-stage05.json"
REVISION = "ade9a02889ef8acbc8cde8edbfd0a785c369f4c3"
EXPECTED = {
    "lp1-06": (823807, "913e26462e51942f49ca3ce2e94ef56c5fb65110814442dccc02b0d88af2c5ca"),
    "lp1-07": (823514, "b50c1536ea1f30847e7875835991d52951bafb599fb1ab04eb78c5c6e6c2b468"),
    "lp1-08": (638805, "f0edba1084df9983353c11544bbf711f94ed7649edbf94b426c9b78549b64557"),
    "lp1-09": (724577, "975cda73bbf829b2775f25beb609d34fa429728b2f2a4ce863c129b10b005089"),
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
        if name not in {"README.md", "avowyfg151kzfj3n.html", "avowyfg151kzfj3n_update_after_downtime.html"}:
            raise ValueError(f"Unexpected source: {name}")
        data = (SOURCE / name).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if (len(data), sha256(data), blob) != (record["bytes"], record["sha256"], record["git_blob_sha1"]):
            raise ValueError(f"Archived source changed: {name}")
        files[name] = data
    if len(files) != 3:
        raise ValueError("Incomplete source manifest")
    return manifest, files


def take_jpeg(data):
    if not data.startswith(bytes([255, 216, 255])):
        raise ValueError("A recovered segment does not start as a JPEG")
    end = data.find(bytes([255, 217])) + 2
    if end < 3:
        raise ValueError("JPEG end marker missing")
    return data[:end], data[end:]


def replay():
    manifest, files = load_sources()
    short = files["avowyfg151kzfj3n.html"]
    match = re.search(rb"<!--3301-->\s*([0-9a-fA-F\s]+?)\s*<hr>", short)
    if not match:
        raise ValueError("Initial capture lacks its 3301-marked hexadecimal body")
    initial = bytes.fromhex(match.group(1).decode("ascii"))
    if len(initial) != 256:
        raise ValueError("Initial capture length changed")
    long = files["avowyfg151kzfj3n_update_after_downtime.html"]
    if not re.fullmatch(rb"[0-9a-fA-F\s]+", long):
        raise ValueError("Later capture contains non-hexadecimal content")
    compressed = bytes.fromhex(long.decode("ascii"))
    if compressed[:2] != bytes([31, 139]):
        raise ValueError("Later capture does not decode to gzip")
    stream = gzip.decompress(compressed)
    first, rest = take_jpeg(stream)
    second, backwards = take_jpeg(rest)
    third, rest = take_jpeg(backwards[::-1])
    fourth, extra = take_jpeg(rest)
    if extra:
        raise ValueError("Unaccounted bytes after four JPEGs")
    outputs = dict(zip(EXPECTED, (first, second, third, fourth)))
    for page, data in outputs.items():
        if (len(data), sha256(data)) != EXPECTED[page] or data != (ROOT / "images" / f"{page}.jpg").read_bytes():
            raise ValueError(f"Recovered page differs from preserved original: {page}")
    report = {
        "schema": "liberpedia-2014-stage05-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
        "initial_response": {"marker": "<!--3301-->", "hex_decoded_bytes": len(initial)},
        "later_response": {"hex_decoded_gzip_bytes": len(compressed), "decompressed_bytes": len(stream),
                           "operation": "Read two forward JPEGs, reverse all remaining bytes, then read two more JPEGs"},
        "images": [{"page": page, "bytes": len(data), "sha256": sha256(data),
                    "byte_direction": "forward" if index < 2 else "reversed remainder",
                    "matches_hosted_original": True}
                   for index, (page, data) in enumerate(outputs.items())],
        "limits": [
            "These are archived captures, not live responses from the historical onion service.",
            "The initial 256-byte body and later gzip response are distinct captures; no update schedule is inferred here.",
            "JPEG equality establishes the source-to-page bytes, not the first koan's reading or the purpose of its embedded payload.",
        ],
    }
    return report, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare replay with published report")
    parser.add_argument("--write", action="store_true", help="Write published report")
    parser.add_argument("--extract-dir", type=Path, help="Save verified JPEGs to a fresh destination")
    args = parser.parse_args()
    if args.check and args.write:
        parser.error("Choose --check or --write")
    report, outputs = replay()
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
    print("Verified LP1-06 through LP1-09 against the archived fourth-onion capture")


if __name__ == "__main__":
    main()
