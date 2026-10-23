"""Independent arithmetic and receipt check for the image-template rebuild.

This checks hashes and reconstructs the line-count alignment from compact
published counts. It does not re-read image pixels or validate rune labels.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def aligned_equal_count(image_lengths, canon_lengths):
    """Reimplement the source's count alignment without importing source code."""
    n, m = len(image_lengths), len(canon_lengths)
    infinity = 10**9
    score = [[infinity] * (m + 1) for _ in range(n + 1)]
    step = [[0] * (m + 1) for _ in range(n + 1)]
    score[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            current = score[i][j]
            if current == infinity:
                continue
            if i < n and j < m:
                trial = current + abs(image_lengths[i] - canon_lengths[j])
                if trial < score[i + 1][j + 1]:
                    score[i + 1][j + 1] = trial
                    step[i + 1][j + 1] = 1
            if i < n and current + 15 < score[i + 1][j]:
                score[i + 1][j] = current + 15
                step[i + 1][j] = 2
            if j < m and current + 15 < score[i][j + 1]:
                score[i][j + 1] = current + 15
                step[i][j + 1] = 3
    matched = exact = skipped_image = 0
    i, j = n, m
    while i or j:
        action = step[i][j]
        if action == 1:
            i -= 1
            j -= 1
            matched += 1
            exact += image_lengths[i] == canon_lengths[j]
        elif action == 2:
            i -= 1
            skipped_image += 1
        elif action == 3:
            j -= 1
        else:
            raise AssertionError(f"Unreachable alignment at {i},{j}")
    return matched, exact, skipped_image


def verify(plan, result, counts):
    assert result["source_revision"] == plan["source_revision"]
    assert result["input_images"] == len(plan["site_images"]) == 56
    assert [int(row["source_name"][1:-4]) for row in plan["site_images"]] == list(range(56))
    assert len(counts["bands"]) == result["fresh"]["bands"] == 646
    assert [row["band"] for row in counts["bands"]] == list(range(646))
    assert len(counts["canon_lengths"]) == 604
    assert sum(counts["canon_lengths"]) == 13136
    assert len(counts["fresh_class_cover"]) == result["fresh"]["shape_classes"] == 229
    assert len(counts["archived_class_cover"]) == result["archived"]["shape_classes"] == 226
    assert sum(counts["fresh_class_cover"]) == result["fresh"]["full_height_glyphs"] == 13140
    assert sum(counts["archived_class_cover"]) == 13140
    assert sum(n >= 100 for n in counts["fresh_class_cover"]) == result["fresh"]["templates_used"] == 33
    assert sum(n >= 100 for n in counts["archived_class_cover"]) == result["archived"]["templates_used"] == 32
    fresh = [row["fresh"] for row in counts["bands"]]
    old = [row["archived"] for row in counts["bands"]]
    assert sum(fresh) == result["fresh"]["read_glyphs"] == 16237
    assert sum(old) == result["archived"]["read_glyphs"] == 16245
    changes = [row for row in counts["bands"] if row["fresh"] != row["archived"]]
    assert changes == result["changed_band_counts"]
    assert len(changes) == 4
    assert aligned_equal_count(fresh, counts["canon_lengths"]) == (596, 233, 50)
    assert aligned_equal_count(old, counts["canon_lengths"]) == (596, 232, 50)
    assert result["fresh"]["aligned_lines"] == 596
    assert result["fresh"]["equal_count_lines"] == 233
    assert result["archived"]["equal_count_lines"] == 232
    assert result["fresh"]["held_out_lines"] == 0
    for key, expected in plan["fresh_control_targets"].items():
        field = {
            "line_bands": "bands",
            "glyph_groups": "component_groups",
            "full_height_glyphs": "full_height_glyphs",
            "distinct_bitmaps": "distinct_bitmaps",
            "shape_classes": "shape_classes",
            "read_glyphs": "read_glyphs",
            "equal_count_lines": "equal_count_lines",
        }[key]
        assert result["fresh"][field] == expected
    for key, expected in plan["historical_comparators"].items():
        assert result["archived"][key] == expected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, help="Verify pinned source and historical receipt bytes")
    parser.add_argument("--site-root", type=Path, help="Verify 56 hosted JPEG bytes")
    parser.add_argument("--artifact-root", type=Path, help="Verify fresh full output-file hashes")
    args = parser.parse_args()
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    counts = json.loads((HERE / "line-counts.json").read_text(encoding="utf-8"))
    verify(plan, result, counts)
    if args.source_root:
        root = args.source_root.resolve()
        for name, expected in {
            **plan["source_code_sha256"],
            **plan["historical_reports_sha256"],
            plan["source_canon_path"]: result["source_canon_sha256"],
        }.items():
            assert sha(root / name) == expected, name
        original = json.loads(
            (root / "analysis/retranscribe/read_lines.json").read_text(encoding="utf-8")
        )
        assert [len(row["glyphs"]) for row in original] == [
            row["archived"] for row in counts["bands"]
        ]
    if args.site_root:
        root = args.site_root.resolve()
        for row in plan["site_images"]:
            path = root / row["site_path"]
            assert path.stat().st_size == row["bytes"]
            assert sha(path) == row["sha256"]
            assert hashlib.sha1(path.read_bytes()).hexdigest() == row["sha1"]
    if args.artifact_root:
        root = args.artifact_root.resolve()
        for name, expected in result["artifact_sha256"].items():
            assert sha(root / name) == expected, name
        actual = json.loads(
            (root / "analysis/retranscribe/read_lines.json").read_text(encoding="utf-8")
        )
        assert [len(row["glyphs"]) for row in actual] == [
            row["fresh"] for row in counts["bands"]
        ]
    print("PASS: 56-image inventory, class totals, 646 band counts, both count alignments, and supplied hashes")
    print("Limit: rune-label agreement is in-sample and no image pixels are independently classified here.")


if __name__ == "__main__":
    main()
