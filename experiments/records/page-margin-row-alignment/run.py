"""Fixed-crop, zero-shift image-row comparison for LP2-40--48."""
from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLAN = HERE / "plan.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure() -> dict:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    x0, y0, x1, y1 = plan["crop"]
    masks = {}
    bands = {}
    for item in plan["inputs"]:
        path = ROOT / item["path"]
        if digest(path) != item["sha256"]:
            raise ValueError(f"source image hash changed: {path}")
        with Image.open(path) as image:
            if image.size != (2400, 3600):
                raise ValueError(f"unexpected image size: {path}")
            px = image.convert("L").load()
            mask = [
                sum(px[x, y] < plan["gray_threshold"] for x in range(x0, x1, plan["x_step"]))
                > plan["minimum_sampled_ink_pixels"]
                for y in range(y0, y1)
            ]
        number = int(path.stem.split("-")[-1])
        masks[number] = mask
        segments = []
        for y, ink in enumerate(mask, y0):
            if ink:
                if segments and segments[-1][-1] == y - 1:
                    segments[-1][-1] = y
                else:
                    segments.append([y, y])
        bands[number] = segments
    pairs = []
    for a, b in combinations(sorted(masks), 2):
        left, right = masks[a], masks[b]
        intersection = sum(x and y for x, y in zip(left, right))
        union = sum(x or y for x, y in zip(left, right))
        pairs.append({
            "left": f"lp2-{a:02}", "right": f"lp2-{b:02}",
            "adjacent": b == a + 1,
            "intersection_rows": intersection, "union_rows": union,
            "jaccard": round(intersection / union, 9) if union else None,
        })
    adjacent = [p["jaccard"] for p in pairs if p["adjacent"]]
    controls = [p["jaccard"] for p in pairs if not p["adjacent"]]
    return {
        "schema": "liberpedia-page-margin-row-alignment-results-v1",
        "crop": plan["crop"], "registration": "original page y; zero offset; no fitting",
        "row_bands": {f"lp2-{n:02}": bands[n] for n in sorted(bands)},
        "pairs": pairs,
        "summary": {
            "adjacent_pairs": len(adjacent), "nonadjacent_controls": len(controls),
            "adjacent_mean": round(sum(adjacent) / len(adjacent), 9),
            "nonadjacent_mean": round(sum(controls) / len(controls), 9),
            "adjacent_perfect": sum(x == 1 for x in adjacent),
            "nonadjacent_perfect": sum(x == 1 for x in controls),
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = measure()
    output = HERE / "results.json"
    if args.check:
        expected = json.loads(output.read_text(encoding="utf-8"))
        if result != expected:
            raise SystemExit("results.json differs from image replay")
        print("Image inputs and 36 pair scores reproduce.")
    else:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result["summary"], indent=2))
