"""Independent row-mask and pair-score check using cropped image byte buffers."""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
report = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
x0, y0, x1, y1 = plan["crop"]
rows = {}
for item in plan["inputs"]:
    name = Path(item["path"]).stem
    with Image.open(ROOT / item["path"]) as image:
        gray = image.convert("L").crop((x0, y0, x1, y1))
        data = gray.tobytes()
    width = x1 - x0
    mask = []
    for y in range(y1 - y0):
        base = y * width
        amount = sum(data[base + x] < plan["gray_threshold"] for x in range(0, width, plan["x_step"]))
        mask.append(amount > plan["minimum_sampled_ink_pixels"])
    rows[name] = mask
    decoded = [False] * len(mask)
    for first, last in report["row_bands"][name]:
        for y in range(first - y0, last - y0 + 1):
            decoded[y] = True
    assert mask == decoded, name
for a, b in combinations(sorted(rows), 2):
    p = next(x for x in report["pairs"] if x["left"] == a and x["right"] == b)
    intersection = sum(v and w for v, w in zip(rows[a], rows[b]))
    union = sum(v or w for v, w in zip(rows[a], rows[b]))
    assert p["intersection_rows"] == intersection
    assert p["union_rows"] == union
    assert p["jaccard"] == round(intersection / union, 9)
assert len(report["pairs"]) == 36
assert sum(p["adjacent"] for p in report["pairs"]) == 8
print("Independent buffer scan: 9 masks and 36 scores agree.")
