"""Test fixed LP2 grid byte readings as complete OpenPGP literal-data packets."""
import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def packet(data):
    """RFC 4880 new-format packet; return stage and literal body if complete."""
    if not data or data[0] != 0xCB:
        return "not-literal-header", None
    p = 1
    body = bytearray()
    while p < len(data):
        length_octet = data[p]
        p += 1
        if length_octet < 192:
            size, final = length_octet, True
        elif length_octet < 224:
            if p == len(data):
                return "truncated-length", None
            size = ((length_octet - 192) << 8) + data[p] + 192
            p += 1
            final = True
        elif length_octet == 255:
            if p + 4 > len(data):
                return "truncated-length", None
            size = int.from_bytes(data[p:p + 4], "big")
            p += 4
            final = True
        else:
            size, final = 1 << (length_octet & 31), False
        if p + size > len(data):
            return "truncated-body", None
        body.extend(data[p:p + size])
        p += size
        if final:
            if p != len(data):
                return "trailing-bytes", None
            if len(body) < 6 or body[0] not in b"btu":
                return "invalid-literal-format", None
            filename_size = body[1]
            if len(body) < 6 + filename_size:
                return "invalid-literal-name", None
            return "complete-literal", bytes(body)
    return "missing-final-length", None


def routes():
    for axis, outer_size, inner_size in (("rows", 32, 8), ("columns", 8, 32)):
        for outer_reverse in (False, True):
            for inner_reverse in (False, True):
                for alternate in (False, True):
                    positions = []
                    outer = list(range(outer_size))
                    if outer_reverse:
                        outer.reverse()
                    for step, outer_index in enumerate(outer):
                        inner = list(range(inner_size))
                        if inner_reverse ^ (alternate and step % 2 == 1):
                            inner.reverse()
                        for inner_index in inner:
                            row, col = (outer_index, inner_index) if axis == "rows" else (inner_index, outer_index)
                            positions.append(row * 8 + col)
                    yield f"{axis}-{int(outer_reverse)}{int(inner_reverse)}{int(alternate)}", positions


def report():
    plan = json.loads((ROOT / "experiments/records/grid-direct-bytes/plan.json").read_text(encoding="utf-8"))
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as handle:
        entries = list(csv.DictReader(handle))
    stems = json.loads((ROOT / "experiments/records/grid-stem-uncertainty/results.json").read_text(encoding="utf-8"))["stem_cells"]
    alpha = plan["digit_alphabet"]
    byte = lambda token: 60 * alpha.index(token[0]) + alpha.index(token[1])
    baseline = [byte(entry["token"]) for entry in entries]
    assert len(baseline) == 256 and len(stems) == 10
    counts = Counter()
    by_route = []
    for name, positions in routes():
        local = Counter()
        for mask in range(1024):
            values = baseline.copy()
            for bit, stem in enumerate(stems):
                values[stem["sequence"] - 1] = stem["base60_bytes"][(mask >> bit) & 1]
            data = bytes(values[i] for i in positions)
            stage, _ = packet(data)
            local[stage] += 1
            counts[stage] += 1
        by_route.append({"route": name, "stage_counts": dict(sorted(local.items()))})
    # A complete, uncompressed literal packet and a valid 128-byte partial chain.
    literal = b"b\x00\x00\x00\x00\x00" + b"hello"
    assert packet(b"\xCB" + bytes([len(literal)]) + literal)[0] == "complete-literal"
    long_literal = literal + b"x" * (129 - len(literal))
    assert packet(b"\xCB\xE7" + long_literal[:128] + b"\x01" + long_literal[128:])[0] == "complete-literal"
    assert packet(b"\xCB\xE7" + long_literal[:128])[0] == "missing-final-length"
    return {
        "schema": "liberpedia-grid-openpgp-literal-v1",
        "cases": 16384,
        "input_sha256": {p: sha256((ROOT / p).read_bytes()).hexdigest() for p in (
            "exports/alphanumeric-grids.csv",
            "experiments/records/grid-direct-bytes/plan.json",
            "experiments/records/grid-stem-uncertainty/results.json")},
        "stage_counts": dict(sorted(counts.items())),
        "routes": by_route,
        "positive_controls": ["complete definite-length packet", "complete 128-byte partial-length packet"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    output = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    path = HERE / "results.json"
    if args.check:
        assert path.read_bytes() == output, "Grid reading or saved result changed"
        assert result["stage_counts"].get("complete-literal", 0) == 0
        print("PASS: 16,384 grid byte readings; OpenPGP literal parser and planted controls")
    else:
        path.write_bytes(output)
        print(result["stage_counts"])


if __name__ == "__main__":
    main()
