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

ROOT = Path(__file__).resolve().parents[1]

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
        count += area >= 20
    return count

def color(crop):
    foreground = red = 0
    for r, g, b in crop.getdata():
        if .299*r + .587*g + .114*b < 140:
            foreground += 1
            red += r - max(g, b) > 70
    ratio = red / foreground if foreground else None
    return "red" if ratio is not None and ratio > .9 else "dark" if ratio is not None and ratio < .1 else "mixed/uncertain"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pixels", action="store_true")
    args = parser.parse_args()
    if args.pixels:
        from PIL import Image
    results = []
    for pid in ["lp2-00", "lp2-01", "lp2-02"]:
        page = json.loads((ROOT / f"data/pages/{pid}.json").read_text(encoding="utf-8"))
        glyphs, marks = page["visual"]["glyphs"], page["visual"]["punctuation"]
        assert [g["ordinal"] for g in glyphs] == list(range(page["rune_count"]))
        width, height = page["image_dimensions"]
        if args.pixels:
            path = ROOT / f"images/{pid}.jpg"
            assert hashlib.sha256(path.read_bytes()).hexdigest() == page["image_sha256"]
            with Image.open(path) as original:
                image = original.convert("RGB")
            assert image.size == (width, height)
        for region in glyphs + marks:
            x, y, w, h = region["rectangle"]
            assert x >= 0 and y >= 0 and w > 0 and h > 0
            assert x+w <= width and y+h <= height
            if args.pixels:
                crop = image.crop((x, y, x+w, y+h))
                assert color(crop) == region["ink_class"], (pid, "color", region)
                if "component_count" in region:
                    pixels = crop.convert("L")
                    points = {(xx, yy) for yy in range(h) for xx in range(w) if pixels.getpixel((xx, yy)) < 140}
                    assert components(points) == region["component_count"], (pid, "components", region)
        results.append(dict(page=pid, glyph_regions=len(glyphs),
                            glyph_colors=dict(Counter(g["ink_class"] for g in glyphs)),
                            punctuation_regions=len(marks),
                            punctuation_component_counts=dict(Counter(g["component_count"] for g in marks))))
    print(json.dumps({"scope": "Stored rectangles; not automatic segmentation or a cipher test.",
                      "pixel_recount": args.pixels, "pages": results}, indent=2))

if __name__ == "__main__":
    main()
