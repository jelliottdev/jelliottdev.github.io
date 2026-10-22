"""Make unenhanced page grabs around the five disputed grid cells.

The rectangles are source-pixel coordinates in the archived seventh-onion JPEGs.
Run `python scripts/capture_seventh_onion_grid.py --check` to verify the hosted
PNG crops and their source hashes without rewriting anything.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/evidence/seventh-onion-grid-crops.json"
REGIONS = {
    49: (560, 2020, 1800, 2480),
    50: (620, 2220, 1800, 2750),
    51: (590, 1620, 1800, 1990),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def build():
    entries = []
    images = {}
    for page, bounds in REGIONS.items():
        source = f"exports/sources/cicada-2014-seventh-onion/{page}.jpg"
        output = f"exports/figures/grid-review-lp2-{page}.png"
        source_bytes = (ROOT / source).read_bytes()
        with Image.open(io.BytesIO(source_bytes)) as image:
            assert image.size == (2400, 3600)
            with io.BytesIO() as buffer:
                image.crop(bounds).save(buffer, format="PNG")
                crop_bytes = buffer.getvalue()
        images[output] = crop_bytes
        entries.append({"page": f"lp2-{page}", "source": source,
                        "source_sha256": sha256(source_bytes),
                        "crop_box_xyxy": bounds, "crop": output,
                        "crop_sha256": sha256(crop_bytes),
                        "operation": "Decode source JPEG and crop its original pixels; no resize, sharpening, or annotation."})
    manifest = {"schema": "liberpedia-seventh-onion-grid-crops-v1",
                "purpose": "Local page grabs for a visual review of five transcription disagreements.",
                "coordinate_system": "Original 2400 × 3600 JPEG pixels; right and bottom bounds exclusive.",
                "entries": entries,
                "limits": "A crop can rule out a visibly dotted or footed character but does not distinguish visually identical uppercase I and lowercase l glyphs."}
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return images, manifest_bytes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    images, manifest_bytes = build()
    outputs = {**{ROOT / path: content for path, content in images.items()},
               MANIFEST: manifest_bytes}
    if args.check:
        for path, content in outputs.items():
            if path.read_bytes() != content:
                raise SystemExit(f"Outdated grid crop: {path}")
        print("Three page grabs and source-hash manifest match the archived JPEGs.")
    else:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        print("Wrote three unenhanced seventh-onion grid page grabs and manifest.")
