"""Independent arithmetic and file-length check for the fixed page lists."""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
p = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
r = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
b = p["reported_big_gap_lp2_pages"]
n = p["reported_regular_gap_comparison_lp2_pages"]
bk = p["reported_size_kb_in_order"]["big_gap"]
nk = p["reported_size_kb_in_order"]["regular_gap"]
assert len(set(b + n)) == 31
assert Fraction(sum(nk), len(nk)) == Fraction(8143, 15)
assert Fraction(sum(bk), len(bk)) == Fraction(9325, 16)
assert r["reported_arithmetic"]["regular_mean_kb_corrected"] == float(Fraction(8143, 15))
assert r["reported_arithmetic"]["big_mean_kb"] == float(Fraction(9325, 16))
for ids, labels in ((b, bk), (n, nk)):
    for page, label in zip(ids, labels):
        image = ROOT / "images" / f"lp2-{page:02d}.jpg"
        assert math.ceil(len(image.read_bytes()) / 1024) == label, page
        assert r["pages"][page]["bytes"] == image.stat().st_size
actual = Fraction(sum(r["pages"][i]["bytes"] for i in b), 16) - Fraction(
    sum(r["pages"][i]["bytes"] for i in n), 15)
assert abs(float(actual) - r["archived_image_bytes"]["mean_difference"]) < 1e-6
print("Independent arithmetic and all 31 source-image size labels match.")
