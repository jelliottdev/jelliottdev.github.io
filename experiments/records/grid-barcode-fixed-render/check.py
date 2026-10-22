"""Independent source and result audit for the fixed-render barcode scan."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import zxingcpp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
source = json.loads((ROOT / "exports/grid-binary-audit.json").read_text(encoding="utf-8"))
with (ROOT / "exports/alphanumeric-grids.csv").open(encoding="utf-8", newline="") as handle:
    tokens = list(csv.DictReader(handle))
assert len(tokens) == 256
rows = []
for group_start in range(0, 256, 8):
    group = tokens[group_start:group_start + 8]
    assert len({(item["page"], item["row"]) for item in group}) == 1
    assert [int(item["column"]) for item in group] == list(range(1, 9))
    values = [60 * ALPHABET.index(token["token"][0]) + ALPHABET.index(token["token"][1]) for token in group]
    assert all(0 <= value <= 255 for value in values)
    rows.append("".join(f"{value:08b}" for value in values))
assert rows == source["bit_rows"]
assert sum(len(row) for row in rows) == 2048
assert report["source_sha256"] == hashlib.sha256((ROOT / "exports/grid-binary-audit.json").read_bytes()).hexdigest()

expected = [rows, rows[:10], rows[10:23], rows[23:]]
assert [case["bit_shape"] for case in report["canvases"]] == [[32, 64], [10, 64], [13, 64], [9, 64]]
for canvas, raw_rows in zip(report["canvases"], expected):
    assert canvas["black_bits"] == sum(row.count("1") for row in raw_rows)
    assert len(canvas["variants"]) == 16
    assert not any(variant["decoded"] for variant in canvas["variants"])
    assert len(report["shuffled_controls"][canvas["canvas"]]) == 8
    for trial in report["shuffled_controls"][canvas["canvas"]]:
        assert not trial["decoded"]

for control in report["positive_controls"]:
    assert len(control["decoded"]) == 1
    assert control["decoded"][0]["format"] == control["format"]
    assert control["decoded"][0]["text"] == control["content"]
    assert control["decoded"][0]["valid"]
assert report["original_scan_count"] == 4 * 16
assert report["shuffled_scan_count"] == 4 * 8 * 16
assert report["original_decode_count"] == report["shuffled_decode_count"] == 0
assert zxingcpp.BarcodeFormat.QRCode and zxingcpp.BarcodeFormat.DataMatrix
print("PASS: independent CSV-to-bits audit; 64 declared scans, 512 shuffles, both positive controls")
