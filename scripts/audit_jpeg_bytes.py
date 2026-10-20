"""Count original LP2 file bytes and inspect baseline JPEG frame headers.

Python standard library only. Does not decode pixels or extract hidden data.
The narrow marker parser fails on unexpected framing rather than guessing.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = "exports/jpeg-byte-audit.json"


def header(data):
    if data[:2] != b"\xff\xd8":
        raise ValueError("Expected JPEG SOI")
    position, frame = 2, None
    while position + 4 <= len(data):
        if data[position] != 255 or data[position + 1] in (0, 255):
            raise ValueError("Unexpected pre-scan marker framing")
        marker = data[position + 1]
        length = int.from_bytes(data[position + 2:position + 4], "big")
        end = position + 2 + length
        if length < 2 or end > len(data):
            raise ValueError("Invalid marker length")
        segment = data[position + 4:end]
        if marker == 0xC0:
            if len(segment) < 6 or len(segment) != 6 + 3 * segment[5]:
                raise ValueError("Malformed SOF0")
            frame = {"marker": "FFC0", "precision_bits": segment[0],
                     "height": int.from_bytes(segment[1:3], "big"),
                     "width": int.from_bytes(segment[3:5], "big"),
                     "components": segment[5]}
        if marker == 0xDA:
            if frame is None:
                raise ValueError("No supported baseline frame before scan")
            return frame, end
        position = end
    raise ValueError("No start-of-scan header")


def report():
    files = []
    for number in range(58):
        path = f"images/lp2-{number:02}.jpg"
        data = (ROOT / path).read_bytes()
        frame, scan_start = header(data)
        counts = Counter(data)
        maximum = max(counts.values())
        files.append({"page": f"lp2-{number:02}", "path": path,
                      "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                      "frame": frame, "first_scan_data_offset": scan_start,
                      "modal_bytes_hex": [f"{v:02X}" for v in range(256) if counts[v] == maximum],
                      "modal_count": maximum, "zero_count": counts[0],
                      "zeros_before_first_scan": data[:scan_start].count(0),
                      "byte_counts_00_through_ff": [counts[v] for v in range(256)]})
    return {"schema": "liberpedia-jpeg-byte-audit-v1",
            "scope": "All 58 archived LP2 JPEG files, complete encoded-file bytes, not decoded pixels or rune indices.",
            "limits": "No randomness test, encoder attribution, hidden-message extraction or LP1 audit.",
            "files": files}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
        print("PASS: all 58 byte histograms, hashes and baseline frame headers")
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    if not args.check and not args.output:
        print(json.dumps(result, indent=2))
