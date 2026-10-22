"""Scan one fixed LP2 grid bit rendering for QR/Data Matrix symbols.

Requires zxing-cpp==3.1.1 and numpy. No network calls or language model.
"""
import argparse
import hashlib
import importlib.metadata
import json
import random
from pathlib import Path

import numpy as np
import zxingcpp


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PLAN = HERE / "plan.json"
SOURCE = ROOT / "exports/grid-binary-audit.json"
RESULT = HERE / "results.json"
FORMATS = (zxingcpp.BarcodeFormat.QRCode, zxingcpp.BarcodeFormat.DataMatrix)
SCALE = 8
QUIET = 4


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canvases(rows):
    assert len(rows) == 32 and all(len(row) == 64 and set(row) <= {"0", "1"} for row in rows)
    return {
        "all-32-rows": rows,
        "lp2-49-10-rows": rows[:10],
        "lp2-50-13-rows": rows[10:23],
        "lp2-51-9-rows": rows[23:],
    }


def matrix(rows):
    return np.array([[int(bit) for bit in row] for row in rows], dtype=np.uint8)


def transforms(bits):
    for mirrored in (False, True):
        reflected = np.fliplr(bits) if mirrored else bits
        for turns in range(4):
            rotated = np.rot90(reflected, turns)
            for inverted in (False, True):
                yield f"mirror-{int(mirrored)}-turns-{turns}-invert-{int(inverted)}", (1 - rotated if inverted else rotated)


def pixels(bits):
    height, width = bits.shape
    image = np.full(((height + 2 * QUIET) * SCALE, (width + 2 * QUIET) * SCALE), 255, dtype=np.uint8)
    image[QUIET * SCALE:(QUIET + height) * SCALE,
          QUIET * SCALE:(QUIET + width) * SCALE] = np.kron(1 - bits, np.ones((SCALE, SCALE), dtype=np.uint8)) * 255
    return image


def decode(image):
    found = zxingcpp.read_barcodes(
        image, formats=FORMATS, try_rotate=False, try_invert=False,
        try_downscale=False, return_errors=False)
    return [{"format": str(hit.format), "text": hit.text, "valid": hit.valid}
            for hit in found if hit.valid and hit.text]


def positive_controls():
    controls = []
    for fmt, expected in ((FORMATS[0], "LP-GRID-QR-CONTROL-3301"),
                          (FORMATS[1], "LP-GRID-DM-CONTROL-3301")):
        barcode = zxingcpp.create_barcode(expected, fmt)
        image = np.asarray(zxingcpp.write_barcode_to_image(barcode, scale=SCALE, add_quiet_zones=True))
        found = decode(image)
        assert len(found) == 1 and found[0]["text"] == expected and found[0]["format"] == str(fmt), (fmt, found)
        controls.append({"format": str(fmt), "content": expected, "image_shape": list(image.shape),
                         "decoded": found})
    return controls


def scan(rows, name):
    bits = matrix(rows)
    cases = []
    for label, transformed in transforms(bits):
        image = pixels(transformed)
        found = decode(image)
        cases.append({"transform": label, "bit_shape": list(transformed.shape),
                      "image_sha256": digest(image.tobytes()), "decoded": found})
    assert len(cases) == 16
    return {"canvas": name, "bit_shape": list(bits.shape), "black_bits": int(bits.sum()),
            "variants": cases}


def shuffled_controls(rows, name):
    original = "".join(rows)
    height, width = len(rows), len(rows[0])
    results = []
    for trial in range(8):
        symbols = list(original)
        random.Random(330100 + trial * 11 + height).shuffle(symbols)
        shuffled = ["".join(symbols[i:i + width]) for i in range(0, len(symbols), width)]
        report = scan(shuffled, name)
        results.append({"trial": trial, "bit_sha256": digest("".join(shuffled).encode("ascii")),
                        "decoded": [{"transform": case["transform"], "hits": case["decoded"]}
                                    for case in report["variants"] if case["decoded"]]})
    return results


def compute():
    assert importlib.metadata.version("zxing-cpp") == "3.1.1", "Pin zxing-cpp 3.1.1 for replay"
    plan_raw = PLAN.read_bytes()
    plan = json.loads(plan_raw)
    source_raw = SOURCE.read_bytes()
    assert digest(source_raw) == plan["inputs"][0]["sha256"]
    source = json.loads(source_raw)
    groups = canvases(source["bit_rows"])
    assert list(groups) == plan["canvases"]
    reports = [scan(rows, name) for name, rows in groups.items()]
    shuffled = {name: shuffled_controls(rows, name) for name, rows in groups.items()}
    return {"schema": "liberpedia-grid-barcode-fixed-render-results-v1",
            "plan_sha256": digest(plan_raw), "source_sha256": digest(source_raw),
            "zxing_cpp": importlib.metadata.version("zxing-cpp"),
            "decoder_settings": {"formats": [str(fmt) for fmt in FORMATS], "try_rotate": False,
                                 "try_invert": False, "try_downscale": False,
                                 "pixel_scale": SCALE, "white_quiet_zone_modules": QUIET},
            "positive_controls": positive_controls(), "canvases": reports,
            "shuffled_controls": shuffled,
            "original_decode_count": sum(len(v["decoded"]) for r in reports for v in r["variants"]),
            "shuffled_decode_count": sum(len(x["hits"]) for rs in shuffled.values() for t in rs for x in t["decoded"]),
            "original_scan_count": sum(len(r["variants"]) for r in reports),
            "shuffled_scan_count": sum(16 * len(rs) for rs in shuffled.values())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = compute()
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        assert RESULT.read_text(encoding="utf-8") == encoded
        print(f"PASS: {report['original_scan_count']} fixed-grid and {report['shuffled_scan_count']} shuffled scans; controls decode")
    else:
        RESULT.write_text(encoded, encoding="utf-8", newline="\n")
        print(f"saved {RESULT}; {report['original_decode_count']} fixed-grid decodes")
