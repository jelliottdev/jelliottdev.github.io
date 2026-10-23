"""Replay a published 56/57-page permutation-window hypothesis on grid bytes."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "source/canon_256.bin"


def window_screen(data, size):
    target = set(range(size))
    near_count = 0
    hits = []
    best_run = 0
    current = 0
    for value in data:
        current = current + 1 if value < size else 0
        best_run = max(best_run, current)
    # A prefix count makes every contiguous-window eligibility test exact and cheap.
    out_of_range = [0]
    for value in data:
        out_of_range.append(out_of_range[-1] + (value >= size))
    for start in range(len(data) - size + 1):
        if out_of_range[start + size] != out_of_range[start]:
            continue
        near_count += 1
        if set(data[start:start + size]) == target:
            hits.append(start)
    return {"windows": len(data) - size + 1, "all_values_in_range": near_count,
            "longest_in_range_run": best_run, "permutation_offsets": hits}


def routes():
    for axis, outer_size, inner_size in (("rows", 32, 8), ("columns", 8, 32)):
        for outer_reverse in (False, True):
            for inner_reverse in (False, True):
                for alternate in (False, True):
                    positions = []
                    outer = list(range(outer_size))
                    if outer_reverse:
                        outer.reverse()
                    for step, row_or_col in enumerate(outer):
                        inner = list(range(inner_size))
                        if inner_reverse ^ (alternate and step % 2):
                            inner.reverse()
                        for col_or_row in inner:
                            row, col = (row_or_col, col_or_row) if axis == "rows" else (col_or_row, row_or_col)
                            positions.append(row * 8 + col)
                    yield f"{axis}-{int(outer_reverse)}{int(inner_reverse)}{int(alternate)}", positions


def report():
    plan = json.loads((ROOT / "experiments/records/grid-direct-bytes/plan.json").read_text(encoding="utf-8"))
    stems = json.loads((ROOT / "experiments/records/grid-stem-uncertainty/results.json").read_text(encoding="utf-8"))["stem_cells"]
    with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    alphabet = plan["digit_alphabet"]
    values0 = [60 * alphabet.index(row["token"][0]) + alphabet.index(row["token"][1]) for row in rows]
    assert len(values0) == 256 and len(stems) == 10
    source = SOURCE.read_bytes()
    assert len(source) == 256 and hashlib.sha256(source).hexdigest() == "4c8dc85531d256793a6d0d318b8845869b4983e672077b094ed955bde92226d5"
    source_screen = {str(n): window_screen(source, n) for n in (56, 57)}
    by_route = []
    for name, positions in routes():
        maximum_run = {56: 0, 57: 0}
        eligible = Counter()
        hits = Counter()
        for mask in range(1024):
            values = values0.copy()
            for bit, stem in enumerate(stems):
                values[stem["sequence"] - 1] = stem["base60_bytes"][(mask >> bit) & 1]
            data = bytes(values[i] for i in positions)
            for n in (56, 57):
                found = window_screen(data, n)
                maximum_run[n] = max(maximum_run[n], found["longest_in_range_run"])
                eligible[n] += found["all_values_in_range"]
                hits[n] += len(found["permutation_offsets"])
        by_route.append({"route": name,
                         "longest_in_range_run": {str(n): maximum_run[n] for n in (56, 57)},
                         "all_values_in_range_windows": {str(n): eligible[n] for n in (56, 57)},
                         "permutation_hits": {str(n): hits[n] for n in (56, 57)}})
    planted = bytearray([255] * 256)
    planted[100:156] = bytes(range(56))
    assert window_screen(planted, 56)["permutation_offsets"] == [100]
    planted[100:157] = bytes(range(57))
    assert window_screen(planted, 57)["permutation_offsets"] == [100]
    return {"schema": "liberpedia-grid-page-order-permutations-v1",
            "source_canon_sha256": hashlib.sha256(source).hexdigest(),
            "source_canon": source_screen,
            "routes": by_route,
            "stream_count": 16384,
            "windows_per_stream": {"56": 201, "57": 200},
            "total_windows": {"56": 16384 * 201, "57": 16384 * 200},
            "positive_controls": ["planted 0–55 at byte 100", "planted 0–56 at byte 100"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = report()
    raw = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check:
        assert (HERE / "results.json").read_bytes() == raw
        assert not result["source_canon"]["56"]["permutation_offsets"]
        assert not result["source_canon"]["57"]["permutation_offsets"]
        assert all(not any(row["permutation_hits"].values()) for row in result["routes"])
        print("PASS: 6,569,984 bounded windows plus the source byte stream and two planted controls")
    else:
        (HERE / "results.json").write_bytes(raw)
        print(result["source_canon"], result["total_windows"])


if __name__ == "__main__":
    main()
