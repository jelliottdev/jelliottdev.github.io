"""Compare fixed original-image windows; no alignment or threshold search.

Python 3 and Pillow are required. Run from an extracted reference-data bundle
with original-images.zip extracted into the same folder, or from the repository.
No image files are modified. --output refuses to replace an existing file.
"""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path

from PIL import Image, features, __version__ as pillow_version

ROOT = Path(__file__).resolve().parents[1]
RESULT = "exports/cuneiform-window-comparison.json"


def measure(root=ROOT):
    windows, pixels = [], {}
    for number in range(33, 40):
        page = f"lp2-{number}"
        path = f"images/{page}.jpg"
        source = (root / path).read_bytes()
        x, y, width, height = 1000, 3030 if number == 33 else 130, 420, 440
        with Image.open(root / path) as image:
            if image.size != (2400, 3600):
                raise ValueError(f"{page}: expected original 2400 x 3600 image")
            rgb = image.convert("RGB").crop((x, y, x + width, y + height))
            pixels[page] = rgb.tobytes()
        windows.append({
            "page": page, "source": path,
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "rectangle_xywh": [x, y, width, height],
            "rgb_sha256": hashlib.sha256(pixels[page]).hexdigest(),
            "pixel_count": width * height,
        })
    comparisons = []
    for left, right in combinations(pixels, 2):
        a, b = pixels[left], pixels[right]
        different = sum(a[i:i + 3] != b[i:i + 3] for i in range(0, len(a), 3))
        comparisons.append({
            "left": left, "right": right,
            "equal_rgb": a == b,
            "different_pixels": different,
            "compared_pixels": len(a) // 3,
            "maximum_channel_difference": max(abs(x - y) for x, y in zip(a, b)),
        })
    return {
        "schema": "liberpedia-fixed-image-window-comparison-v1",
        "purpose": "Descriptive measurement of seven fixed windows, not a decipherment",
        "decoder": {"pillow": pillow_version, "jpeg": features.version_codec("jpg")},
        "method": "Decode JPEG to RGB; compare corresponding RGB triples exactly. "
                  "No rotation, reflection, resizing, alignment search, threshold, or tolerance.",
        "selection": "Existing guide windows for LP2-33 and LP2-34; "
                     "the LP2-34 window reused on LP2-35–39 after visual inspection. "
                     "Exploratory equality was observed before this report script was written.",
        "windows": windows,
        "comparisons": comparisons,
        "equal_pairs": sum(c["equal_rgb"] for c in comparisons),
        "pair_count": len(comparisons),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    actual = measure()
    if args.check:
        expected = json.loads((ROOT / RESULT).read_text(encoding="utf-8"))
        # Decoder versions are provenance, not a requirement to install an old build.
        # Any resulting pixel or file-hash difference must still fail the check.
        expected_decoder = expected.pop("decoder")
        actual_decoder = actual.pop("decoder")
        if actual != expected:
            raise SystemExit("FAIL: sources or measured windows differ from the recorded report")
        print(f"PASS: all seven source hashes and all {actual['pair_count']} pair comparisons reproduce")
        print(f"Decoder: current {actual_decoder}; recorded {expected_decoder}")
    elif args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(actual, handle, indent=2)
            handle.write("\n")
    else:
        print(json.dumps(actual, indent=2))


if __name__ == "__main__":
    main()
