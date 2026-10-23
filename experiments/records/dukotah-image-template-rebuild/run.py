"""Inspect or rebuild the pinned Dukotah LP2 image-template pipeline.

The four source algorithms are copied byte-for-byte into an isolated directory.
This wrapper checks their hashes and the 56 image bytes before running them.
The expensive rebuild is opt-in and never overwrites the published receipts.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def verify_source(source_root, site_root):
    for name, expected in PLAN["source_code_sha256"].items():
        actual = digest(source_root / name)
        if actual != expected:
            raise ValueError(f"Source hash mismatch: {name}: {actual}")
    for name, expected in PLAN["historical_reports_sha256"].items():
        actual = digest(source_root / name)
        if actual != expected:
            raise ValueError(f"Historical receipt hash mismatch: {name}: {actual}")
    for row in PLAN["site_images"]:
        path = site_root / row["site_path"]
        if path.stat().st_size != row["bytes"]:
            raise ValueError(f"Image byte-count mismatch: {path}")
        if digest(path) != row["sha256"] or digest(path, "sha1") != row["sha1"]:
            raise ValueError(f"Image hash mismatch: {path}")


def isolated_rebuild(source_root, site_root, target):
    for name in PLAN["source_code_sha256"]:
        dst = target / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / name, dst)
    for row in PLAN["site_images"]:
        dst = target / "data/relikd" / row["source_name"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(site_root / row["site_path"], dst)
    env = dict(os.environ)
    env["OPENBLAS_NUM_THREADS"] = "4"
    for name in PLAN["stage_order"]:
        subprocess.run([sys.executable, name], cwd=target, env=env, check=True)


def canon_lengths(source_root):
    sys.path.insert(0, str(source_root / "src"))
    from lp.gematria import RUNE_TO_IDX
    text = (source_root / PLAN["source_canon_path"]).read_text(encoding="utf-8")
    lines = [
        [RUNE_TO_IDX[ch] for ch in line if ch in RUNE_TO_IDX]
        for section in text.split("%") for line in section.split("/")
    ]
    return [len(line) for line in lines if line]


def summary(source_root, artifact_root):
    import numpy as np

    geo = np.load(artifact_root / "analysis/geometry/glyphs2.npz")
    template = np.load(artifact_root / "analysis/retranscribe/templates.npz")
    report = json.loads((artifact_root / "analysis/retranscribe/templates_report.json").read_text())
    historical_report = json.loads(
        (source_root / "analysis/retranscribe/templates_report.json").read_text()
    )
    read = json.loads((artifact_root / "analysis/retranscribe/read_lines.json").read_text())
    historical_read = json.loads(
        (source_root / "analysis/retranscribe/read_lines.json").read_text()
    )
    diff = json.loads((artifact_root / "analysis/retranscribe/diff_report.json").read_text())
    historical_diff = json.loads(
        (source_root / "analysis/retranscribe/diff_report.json").read_text()
    )
    if len(read) != len(historical_read):
        raise ValueError("Different line-band counts")
    bands = geo["bands"]
    rows = []
    for index, (current, old) in enumerate(zip(read, historical_read)):
        if current["page"] != old["page"] or current["band"] != old["band"]:
            raise ValueError(f"Band identity mismatch at {index}")
        rows.append({
            "band": index,
            "page": int(current["page"]),
            "fresh": len(current["glyphs"]),
            "archived": len(old["glyphs"]),
        })
    compact = {
        "schema": "liberpedia-template-line-counts-v1",
        "bands": rows,
        "canon_lengths": canon_lengths(source_root),
        "fresh_class_cover": report["class_glyph_counts"],
        "archived_class_cover": historical_report["class_glyph_counts"],
    }
    artifacts = [
        "analysis/geometry/glyphs2.npz",
        "analysis/retranscribe/templates.npz",
        "analysis/retranscribe/templates_report.json",
        "analysis/retranscribe/read_lines.json",
        "analysis/retranscribe/diff_report.json",
    ]
    output = {
        "schema": "liberpedia-image-template-rebuild-results-v1",
        "source_revision": PLAN["source_revision"],
        "input_images": len(PLAN["site_images"]),
        "fresh": {
            "bands": len(bands),
            "component_groups": int(len(geo["page"])),
            "full_height_glyphs": int(sum(report["class_glyph_counts"])),
            "distinct_bitmaps": int(report["n_bitmaps"]),
            "shape_classes": int(report["n_classes"]),
            "templates_used": sum(n >= 100 for n in report["class_glyph_counts"]),
            "read_glyphs": sum(row["fresh"] for row in rows),
            "aligned_lines": int(diff["aligned"]),
            "equal_count_lines": int(diff["exact_lines"]),
            "in_sample_agreement_percent": float(diff["agreement"]),
            "in_sample_compared_glyphs": int(diff["compared"]),
            "held_out_lines": 0,
        },
        "archived": {
            "shape_classes": int(historical_report["n_classes"]),
            "templates_used": sum(n >= 100 for n in historical_report["class_glyph_counts"]),
            "read_glyphs": sum(row["archived"] for row in rows),
            "equal_count_lines": int(historical_diff["exact_lines"]),
            "in_sample_agreement_percent": float(historical_diff["agreement"]),
        },
        "changed_band_counts": [
            row for row in rows if row["fresh"] != row["archived"]
        ],
        "artifact_sha256": {name: digest(artifact_root / name) for name in artifacts},
        "source_canon_sha256": digest(source_root / PLAN["source_canon_path"]),
        "notes": [
            "The archived NPZ arrays have no published hashes, so array identity cannot be checked.",
            "The class-to-rune map is fitted and scored on the same LP2 canonical lines; its percentage is in-sample.",
        ],
    }
    return output, compact


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--site-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, help="Previously rebuilt isolated source tree")
    parser.add_argument("--rebuild", action="store_true", help="Run all four original scripts in a temporary tree")
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--check", action="store_true", help="Compare to the frozen public receipts")
    args = parser.parse_args()
    source = args.source_root.resolve()
    site = args.site_root.resolve()
    verify_source(source, site)
    if args.rebuild == bool(args.artifact_root):
        parser.error("Choose exactly one of --rebuild or --artifact-root")
    if args.rebuild:
        with tempfile.TemporaryDirectory(prefix="lp2-template-rebuild-") as temporary:
            target = Path(temporary)
            isolated_rebuild(source, site, target)
            output, compact = summary(source, target)
    else:
        output, compact = summary(source, args.artifact_root.resolve())
    if args.check:
        expected = json.loads((HERE / "results.json").read_text())
        counts = json.loads((HERE / "line-counts.json").read_text())
        if output != expected or compact != counts:
            raise SystemExit("Fresh summary differs from frozen receipts")
        print("PASS: image/source hashes, artifact summary and line counts")
    else:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "results.json", output)
        write_json(args.output_dir / "line-counts.json", compact)
        print("Wrote results and line-count receipts:", args.output_dir)


if __name__ == "__main__":
    main()
