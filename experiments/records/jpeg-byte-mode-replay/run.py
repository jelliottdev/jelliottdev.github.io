"""Recount archived JPEG byte modes and component counts. Standard library only."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def jpeg_header(data):
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("Not a JPEG")
    pos = 2
    components = None
    while pos + 4 <= len(data):
        if data[pos] != 255 or data[pos + 1] in (0, 255):
            raise ValueError("Unexpected marker before first scan")
        marker = data[pos + 1]
        length = int.from_bytes(data[pos + 2:pos + 4], "big")
        end = pos + 2 + length
        if length < 2 or end > len(data):
            raise ValueError("Invalid marker length")
        if marker == 0xC0:
            segment = data[pos + 4:end]
            if len(segment) < 6 or len(segment) != 6 + 3 * segment[5]:
                raise ValueError("Invalid baseline frame")
            components = segment[5]
        if marker == 0xDA:
            if components is None:
                raise ValueError("No baseline frame before first scan")
            return components, end
        pos = end
    raise ValueError("No first scan")


def analyze():
    rows = []
    for release, count in (("lp2", 58), ("lp1", 17)):
        for number in range(count):
            page = f"{release}-{number:02}"
            data = (ROOT / "images" / f"{page}.jpg").read_bytes()
            components, first_scan = jpeg_header(data)
            freq = Counter(data)
            peak = max(freq.values())
            rows.append({
                "page": page,
                "sha256": sha256(data).hexdigest(),
                "bytes": len(data),
                "modal_bytes": [f"{byte:02X}" for byte in range(256) if freq[byte] == peak],
                "mode_count": peak,
                "zero_count": freq[0],
                "zero_share": round(freq[0] / len(data), 6),
                "zero_count_before_first_scan": data[:first_scan].count(0),
                "components": components,
            })
    return {"schema": "liberpedia-jpeg-byte-mode-replay-v1", "files": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = analyze()
    if args.check:
        expected = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
        assert result == expected, "Archived image bytes or recorded results changed"
        lp2 = result["files"][:58]
        lp1 = result["files"][58:]
        assert [x["page"] for x in lp2 if x["modal_bytes"] != ["00"]] == ["lp2-00", "lp2-04", "lp2-24", "lp2-26"]
        assert [x["page"] for x in lp1 if x["modal_bytes"] != ["00"]] == ["lp1-00", "lp1-02"]
        assert all(len(x["modal_bytes"]) == 1 for x in result["files"])
        assert {x["components"] for x in lp2 if x["modal_bytes"] == ["00"]} == {1, 3}
        assert {x["components"] for x in lp2 if x["modal_bytes"] == ["44"]} == {1, 3}
        assert all(x["zero_count_before_first_scan"] < x["zero_count"] for x in result["files"])
        print("PASS: 75 original JPEG hashes, modes, zero counts and frame components")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
