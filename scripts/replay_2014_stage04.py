"""Replay the archived 2014 responses that supplied LP1-03 through LP1-05."""

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "exports/sources/cicada-2014-stage04"
REPORT = ROOT / "exports/cicada-2014-stage04.json"
REVISION = "10733feb487bb8beb9966d534727ee5897aa54fc"
EXPECTED = {
    "lp1-03": (892759, "b8b142f9b7854ec4f240e076cad03a98a2e3e9cf7c20f1da4fcde1ed25e3be3f"),
    "lp1-04": (1223337, "745c6a46f67de1e5a2a9ac76175c323af82c2432e3b7483a8dc6244f8de9478f"),
    "lp1-05": (673066, "2db94921ae5216d8a589890495fa5432446cd3227c45fbeb4934cbb0525112f7"),
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
        if name not in {"README.md", "index.html", "index.html.1", "server-status", "matrix.txt"}:
            raise ValueError(f"Unexpected source file: {name}")
        data = (SOURCE / name).read_bytes()
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if (len(data), sha256(data), blob) != (record["bytes"], record["sha256"], record["git_blob_sha1"]):
            raise ValueError(f"Archived source changed: {name}")
        files[name] = data
    if set(files) != {"README.md", "index.html", "index.html.1", "server-status", "matrix.txt"}:
        raise ValueError("Source manifest incomplete")
    return manifest, files


def decode_index(data, marker):
    lines = data.splitlines()
    if not lines or lines[0] != marker:
        raise ValueError("Unexpected index marker")
    return bytes.fromhex(b"".join(lines[1:]).decode("ascii"))


def replay():
    manifest, files = load_sources()
    short = decode_index(files["index.html"], b"<!--1033-->")
    joined = decode_index(files["index.html.1"], b"<!--3301-->")
    if len(short) != 256 or len(joined) != 2116096:
        raise ValueError("Unexpected index lengths")
    status = re.search(rb"<pre>\s*([0-9a-fA-F\s]+?)\s*</pre>", files["server-status"], re.DOTALL)
    if not status or len(re.findall(rb"<pre>", files["server-status"])) != 1:
        raise ValueError("Expected one hexadecimal pre block in server-status")
    page05 = bytes.fromhex(status.group(1).decode("ascii"))
    outputs = {
        "lp1-03": joined[:892759],
        "lp1-04": joined[::-1][:1223337],
        "lp1-05": page05,
    }
    for page, data in outputs.items():
        if (len(data), sha256(data)) != EXPECTED[page] or data != (ROOT / "images" / f"{page}.jpg").read_bytes():
            raise ValueError(f"Recovered page differs from original: {page}")
    matrix_bytes = bytes.fromhex(page05[336353:336713][::-1].decode("ascii"))
    if matrix_bytes != files["matrix.txt"]:
        raise ValueError("Extracted matrix differs from archived matrix")
    matrix = [[int(cell) for cell in row.split()] for row in matrix_bytes.decode("ascii").splitlines()]
    if len(matrix) != 5 or any(len(row) != 5 for row in matrix):
        raise ValueError("Expected a five-by-five matrix")
    sums = [sum(row) for row in matrix] + [sum(row[col] for row in matrix) for col in range(5)]
    sums += [sum(matrix[i][i] for i in range(5)), sum(matrix[i][4 - i] for i in range(5))]
    if sums != [1033] * 12:
        raise ValueError("Matrix line sums changed")
    report = {
        "schema": "liberpedia-2014-stage04-replay-v1",
        "source_revision": manifest["revision"],
        "source_manifest_sha256": sha256((SOURCE / "manifest.json").read_bytes()),
        "source_files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
        "index_captures": {"initial_marker": "<!--1033-->", "initial_hex_decoded_bytes": len(short),
                           "later_marker": "<!--3301-->", "later_hex_decoded_bytes": len(joined),
                           "initial_is_prefix_of_later": joined.startswith(short)},
        "images": [
            {"page": page, "bytes": len(data), "sha256": sha256(data), "matches_hosted_original": True,
             "extraction": "first 892759 bytes of later decoded index" if page == "lp1-03" else
                           "first 1223337 bytes after reversing entire later decoded index" if page == "lp1-04" else
                           "hex decode of the server-status pre block"}
            for page, data in outputs.items()
        ],
        "embedded_matrix": {"page": "lp1-05", "offset": 336353, "reversed_hex_slice_bytes": 360,
                            "decoded_bytes": len(matrix_bytes), "sha256": sha256(matrix_bytes),
                            "values": matrix, "row_column_diagonal_sums": sums},
        "limits": [
            "These files are archived captures, not live responses from the historical service.",
            "The 256-byte initial index capture is recorded separately; no update schedule is inferred.",
            "The matrix repeats the known LP1-05 values; its extraction does not supply a new unsolved-page key.",
        ],
    }
    return report, outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare replay with published report")
    parser.add_argument("--write", action="store_true", help="Write published report")
    parser.add_argument("--extract-dir", type=Path, help="Save verified JPEGs to an empty destination")
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
    print("Verified LP1-03, LP1-04, LP1-05 and the LP1-05 embedded matrix")


if __name__ == "__main__":
    main()
