"""Audit reported size arithmetic and archived LP2 JPEG bytes, not gap geometry.

Standard-library only. Requires original-images.zip extracted beside the
reference-data bundle, or a repository checkout. No network or image edits.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = "exports/gap-file-sizes.json"
GAPS = [4, 7, 10, 21, 22, 35, 36, 37, 38, 41, 42, 43, 51, 53, 56, 57]
COMPARISON = [0, 1, 8, 15, 17, 18, 19, 20, 14, 23, 26, 27, 28, 32, 3]
REPORTED_GAPS = [661, 568, 604, 539, 501, 562, 500, 493, 508, 768, 771, 774, 647, 737, 381, 311]
REPORTED_COMPARISON = [680, 652, 599, 501, 529, 530, 528, 524, 427, 473, 662, 567, 530, 355, 586]


def summary(values):
    mean = Fraction(sum(values), len(values))
    return {"count": len(values), "sum": sum(values), "mean_exact": str(mean),
            "mean": float(mean)}


def report():
    assert len(GAPS) == len(REPORTED_GAPS) == 16
    assert len(COMPARISON) == len(REPORTED_COMPARISON) == 15
    assert not set(GAPS) & set(COMPARISON)
    rows = []
    for number in range(58):
        path = f"images/lp2-{number:02}.jpg"
        data = (ROOT / path).read_bytes()
        rows.append({"page": f"lp2-{number:02}", "path": path,
                     "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                     "reported_group": "gap" if number in GAPS else
                     "comparison" if number in COMPARISON else "unlisted"})
    return {
        "schema": "liberpedia-gap-size-audit-v1",
        "scope": "Historical reported groups; no independent gap classification, pixel measurement, or significance test.",
        "historical_units": "The source labels its rounded values kb; no byte-unit convention is assumed.",
        "reported_gap_pages": GAPS, "reported_comparison_pages": COMPARISON,
        "reported_gap_values": REPORTED_GAPS,
        "reported_comparison_values": REPORTED_COMPARISON,
        "reported_gap_summary": summary(REPORTED_GAPS),
        "reported_comparison_summary": summary(REPORTED_COMPARISON),
        "reported_difference_exact": str(Fraction(sum(REPORTED_GAPS),16)-Fraction(sum(REPORTED_COMPARISON),15)),
        "reported_comparison_sum_divided_by_16": str(Fraction(sum(REPORTED_COMPARISON),16)),
        "archived_gap_bytes": summary([r["bytes"] for r in rows if r["reported_group"] == "gap"]),
        "archived_comparison_bytes": summary([r["bytes"] for r in rows if r["reported_group"] == "comparison"]),
        "files": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare with the shipped JSON report")
    parser.add_argument("--output", type=Path, help="Write a new report; refuses to overwrite")
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
        print("PASS: reported arithmetic and all 58 original JPEG sizes and hashes")
    if args.output:
        with args.output.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    if not args.check and not args.output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
