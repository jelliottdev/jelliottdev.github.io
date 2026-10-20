"""Check LP2-00..02's published region inventory; optionally recount pixels.

Default: Python standard library, structural checks and stored counts.
--pixels: requires Pillow; checks original image hashes, region colors, and
eight-connected components within the stored punctuation bounding rectangles.
This does not discover regions, redo the transcription, or infer cipher rules.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
BRIGHTNESS_LIMIT = 140
MINIMUM_AREA = 20
RED_MARGIN = 70

def require(condition, message):
    if not condition:
        raise ValueError(message)

def components(points):
    remaining = set(points)
    count = 0
    while remaining:
        pending = [remaining.pop()]
        area = 0
        while pending:
            x, y = pending.pop()
            area += 1
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    neighbor = (x + dx, y + dy)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        pending.append(neighbor)
        count += area >= MINIMUM_AREA
    return count

def color(crop):
    foreground = red = 0
    for r, g, b in crop.getdata():
        if .299*r + .587*g + .114*b < BRIGHTNESS_LIMIT:
            foreground += 1
            red += r - max(g, b) > RED_MARGIN
    ratio = red / foreground if foreground else None
    return "red" if ratio is not None and ratio > .9 else "dark" if ratio is not None and ratio < .1 else "mixed/uncertain"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixels", action="store_true")
    args = parser.parse_args()
    pillow_version = None
    if args.pixels:
        from PIL import Image
        from PIL import __version__ as pillow_version
    results = []
    for pid in ["lp2-00", "lp2-01", "lp2-02"]:
        record_path = f"data/pages/{pid}.json"
        record_bytes = (ROOT / record_path).read_bytes()
        page = json.loads(record_bytes)
        glyphs, marks = page["visual"]["glyphs"], page["visual"]["punctuation"]
        require([g["ordinal"] for g in glyphs] == list(range(page["rune_count"])),
                f"{pid}: glyph ordinals do not match rune_count")
        width, height = page["image_dimensions"]
        if args.pixels:
            path = ROOT / f"images/{pid}.jpg"
            require(hashlib.sha256(path.read_bytes()).hexdigest() == page["image_sha256"],
                    f"{pid}: original image SHA-256 mismatch")
            with Image.open(path) as original:
                image = original.convert("RGB")
            require(image.size == (width, height), f"{pid}: image dimensions mismatch")
        for region_index, region in enumerate(glyphs + marks):
            label = f"{pid}: region {region_index} (glyphs followed by punctuation)"
            x, y, w, h = region["rectangle"]
            require(all(type(value) is int for value in (x, y, w, h)),
                    f"{label}: rectangle coordinates must be integers")
            require(x >= 0 and y >= 0 and w > 0 and h > 0,
                    f"{label}: rectangle must have nonnegative origin and positive size")
            require(x+w <= width and y+h <= height, f"{label}: rectangle exceeds image bounds")
            if args.pixels:
                crop = image.crop((x, y, x+w, y+h))
                require(color(crop) == region["ink_class"], f"{label}: ink class mismatch")
                if "component_count" in region:
                    pixels = crop.convert("L")
                    points = {(xx, yy) for yy in range(h) for xx in range(w) if pixels.getpixel((xx, yy)) < BRIGHTNESS_LIMIT}
                    require(components(points) == region["component_count"],
                            f"{label}: component count mismatch")
        results.append(dict(page=pid,
                            record_path=record_path,
                            record_sha256=hashlib.sha256(record_bytes).hexdigest(),
                            image_path=f"images/{pid}.jpg",
                            expected_image_sha256=page["image_sha256"],
                            image_hash_verified=args.pixels,
                            image_dimensions=[width, height],
                            glyph_regions=len(glyphs),
                            glyph_colors=dict(Counter(g["ink_class"] for g in glyphs)),
                            punctuation_regions=len(marks),
                            punctuation_component_counts=dict(Counter(g["component_count"] for g in marks))))
    print(json.dumps({"schema_version": 1,
                      "scope": "Stored rectangles; not automatic segmentation or a cipher test.",
                      "pillow_version": pillow_version,
                      "rules": {
                          "rectangles": "[x, y, width, height], original pixels, top-left origin; right/bottom excluded",
                          "component_grayscale": "Pillow RGB.convert('L')",
                          "foreground_strictly_below": BRIGHTNESS_LIMIT,
                          "connectivity": 8,
                          "minimum_component_area_pixels": MINIMUM_AREA,
                          "color_foreground": f"0.299R + 0.587G + 0.114B < {BRIGHTNESS_LIMIT} (unrounded)",
                          "red_dominance_strictly_above": RED_MARGIN,
                          "red_dominance_expression": "R - max(G, B)",
                          "red_fraction_strictly_above": .9,
                          "dark_fraction_strictly_below": .1,
                          "otherwise": "mixed/uncertain, including no foreground",
                      },
                      "pixel_recount": args.pixels, "pages": results}, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(f"Visual verification failed: {error}", file=sys.stderr)
        sys.exit(1)
