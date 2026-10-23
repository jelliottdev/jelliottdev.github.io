#!/usr/bin/env python3
"""Audit the red-initial detector used in a public LP2 experiment.

Run from the repository root with Pillow, NumPy and OpenCV installed:
    python scripts/audit_red_initials.py > research/red-initials-audit.csv

This is a *shape audit*, not a decryption or a significance test. The red
threshold matches the source detector. Components are independently measured
at half resolution with four-neighbour connectivity. A count of coloured
pixels can be large because of many ordinary red runes on a page.
"""

import csv
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RED_COUNT_MIN = 30_000  # source's rule; inclusive in its implementation
LARGE_COMPONENT_MIN = 10_000  # full-resolution-equivalent pixels


def inspect(path):
    raw = path.read_bytes()
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    red = (r > 120) & (g < 90) & (b < 90) & (r - g > 60) & (r - b > 60)
    red_pixels = int(red.sum())

    # Recompute shape independently of the source's ::4 labeller. At this
    # resolution one sampled pixel represents four full-resolution pixels.
    sampled = red[::2, ::2].astype(np.uint8)
    count, _, stats, _ = cv2.connectedComponentsWithStats(sampled, connectivity=4)
    if count > 1:
        foreground = stats[1:, cv2.CC_STAT_AREA]
        largest = int(foreground.max()) * 4
        large_count = int((foreground * 4 >= LARGE_COMPONENT_MIN).sum())
    else:
        largest = large_count = 0
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "red_pixels": red_pixels,
        "source_total_rule": int(red_pixels >= RED_COUNT_MIN),
        "largest_red_component_px_equiv": largest,
        "large_component_count": large_count,
        "component_rule": int(large_count > 0),
    }


def main():
    writer = csv.DictWriter(sys.stdout, fieldnames=[
        "page", "sha256", "red_pixels", "source_total_rule",
        "largest_red_component_px_equiv", "large_component_count",
        "component_rule",
    ], lineterminator="\n")
    writer.writeheader()
    for page in range(58):
        path = ROOT / "images" / f"lp2-{page:02d}.jpg"
        if not path.is_file():
            raise SystemExit(f"missing archived image: {path}")
        writer.writerow({"page": f"LP2-{page:02d}", **inspect(path)})


if __name__ == "__main__":
    main()
