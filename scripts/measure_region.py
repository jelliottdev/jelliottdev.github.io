"""Measure connected foreground pixels in an original manuscript rectangle.

Requires Pillow. Read-only: reports JSON to stdout; never modifies image files.
Centroids describe threshold-selected pixels, not inferred semantic dot centers.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def component_records(points, connectivity=8, minimum_area=20):
    if connectivity not in (4, 8) or minimum_area < 1:
        raise ValueError("Use connectivity 4 or 8 and a positive minimum area")
    neighbors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    if connectivity == 8:
        neighbors += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    remaining = set(points)
    kept, discarded = [], 0
    while remaining:
        seed = remaining.pop()
        pending = [seed]
        area = sx = sy = 0
        left = right = seed[0]
        top = bottom = seed[1]
        while pending:
            x, y = pending.pop()
            area += 1
            sx += x
            sy += y
            left, right = min(left, x), max(right, x)
            top, bottom = min(top, y), max(bottom, y)
            for dx, dy in neighbors:
                neighbor = (x + dx, y + dy)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        if area < minimum_area:
            discarded += 1
            continue
        kept.append({"area_pixels": area,
                     "bounds": [left, top, right - left + 1, bottom - top + 1],
                     "centroid": [round(sx / area, 6), round(sy / area, 6)]})
    kept.sort(key=lambda r: (r["centroid"][1], r["centroid"][0]))
    return kept, discarded


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", help="Release ID, for example lp2-56")
    parser.add_argument("--rect", type=int, nargs=4, required=True,
                        metavar=("X", "Y", "WIDTH", "HEIGHT"))
    parser.add_argument("--threshold", type=int, default=140,
                        help="Foreground grayscale strictly below this value (1..255)")
    parser.add_argument("--minimum-area", type=int, default=20)
    parser.add_argument("--connectivity", type=int, choices=[4, 8], default=8)
    args = parser.parse_args()
    if not re.fullmatch(r"lp[12]-[0-9]{2}", args.page):
        parser.error("Use a release page ID such as lp2-56")
    if not 1 <= args.threshold <= 255 or args.minimum_area < 1:
        parser.error("Threshold must be 1..255; minimum area must be positive")
    record_path = ROOT / "data/pages" / (args.page + ".json")
    if not record_path.is_file():
        parser.error("No page record for this ID")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    image_path = ROOT / "images" / (args.page + ".jpg")
    if not image_path.is_file():
        parser.error("Original JPEG missing; extract original-images.zip beside the reference data")
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    if digest != record["image_sha256"]:
        parser.error("Original image SHA-256 differs from the page record")
    try:
        from PIL import Image, __version__ as pillow_version
    except ImportError:
        parser.error("Pillow is required: python -m pip install Pillow")
    with Image.open(image_path) as original:
        width, height = original.size
        x, y, w, h = args.rect
        if min(x, y) < 0 or min(w, h) <= 0 or x + w > width or y + h > height:
            parser.error("Rectangle must have positive dimensions and lie inside the original image")
        gray = original.convert("RGB").convert("L").crop((x, y, x + w, y + h))
        points = {(x + i % w, y + i // w) for i, value in enumerate(gray.getdata())
                  if value < args.threshold}
    components, discarded = component_records(points, args.connectivity, args.minimum_area)
    print(json.dumps({
        "page": args.page, "image_sha256": digest,
        "image_dimensions": [width, height], "rect": args.rect,
        "pillow_version": pillow_version,
        "rules": {"grayscale": "Pillow RGB.convert('L')",
                  "foreground_strictly_below": args.threshold,
                  "connectivity": args.connectivity, "minimum_area_pixels": args.minimum_area,
                  "coordinates": "Original pixels; integer pixel indices; bounds are [x,y,width,height] with right/bottom excluded",
                  "centroid": "Arithmetic mean of selected pixel indices, rounded to six decimals; components sorted by centroid y then x"},
        "foreground_pixels": len(points), "component_count": len(components),
        "discarded_small_components": discarded, "components": components,
        "scope": "Pixel measurement only; no symbol identification, source attribution or cipher claim."
    }, indent=2))


if __name__ == "__main__":
    main()
