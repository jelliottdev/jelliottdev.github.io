"""Re-run pinned T2 code with a fresh, explicitly identified template bank.

The source algorithms are copied unchanged to an isolated temporary tree. This
wrapper verifies bytes, executes the source controls, and emits compact receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SOURCE_FILES = ["analysis/round19/T2/t2lib.py", "analysis/round19/T2/linemap.py",
                "analysis/round19/T2/probe.py", "analysis/round19/T2/score.py",
                "src/lp/gematria.py"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(path, digest):
    if not path.is_file() or sha(path) != digest:
        raise ValueError(f"Missing or changed input: {path}")


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def compact(fresh, historical):
    if len(fresh) != len(historical) or len(fresh) != 604:
        raise ValueError("Expected 604 aligned T2 rows")
    rows = []
    for a, b in zip(fresh, historical):
        if a["gline"] != b["gline"]:
            raise ValueError("T2 line order changed")
        rows.append({
            "gline": a["gline"], "seg": a.get("seg"), "num": a.get("num"),
            "nrune": a.get("nrune"), "skip0": a.get("skip0"),
            "canon": a.get("canon"), "fresh_best": a.get("best"),
            "historical_best": b.get("best"),
            "fresh_best_cost": a.get("best_cost"),
            "fresh_canon_cost": a.get("canon_cost"),
            "historical_best_cost": b.get("best_cost"),
            "historical_canon_cost": b.get("canon_cost"),
            "fresh_x": a.get("x"), "historical_x": b.get("x"),
            "fresh_fail": a.get("fail"), "historical_fail": b.get("fail"),
        })
    return rows


def verify_inputs(plan, source, site):
    for rel, digest in plan["source_code_sha256"].items():
        require(source / rel, digest)
    require(source / plan["source_canon"]["path"], plan["source_canon"]["sha256"])
    for rel, digest in plan["historical_output_sha256"].items():
        require(source / rel, digest)
    for item in plan["images"]:
        p = site / item["site_path"]
        require(p, item["sha256"])
        if p.stat().st_size != item["bytes"]:
            raise ValueError(f"Unexpected image size: {p}")
    require(HERE / "templates.npz", plan["fresh_instrument"]["templates_npz_sha256"])
    require(HERE / "diff_report.json", plan["fresh_instrument"]["diff_report_sha256"])


def build_tree(temp, plan, source, site):
    lp = temp / "liber-primus"
    for rel in SOURCE_FILES + [plan["source_canon"]["path"]]:
        target = lp / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / rel, target)
    rt = lp / "analysis/retranscribe"
    rt.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "templates.npz", rt / "templates.npz")
    shutil.copyfile(HERE / "diff_report.json", rt / "diff_report.json")
    vendor = temp / "corpus/E-tooling/vendor/cicada-solvers__documenting-cicada3301-scream314/assets/2014/liber-primus-complete"
    relikd = lp / "data/relikd"
    relikd.mkdir(parents=True, exist_ok=True)
    vendor.mkdir(parents=True, exist_ok=True)
    for item in plan["images"]:
        name = item.get("source_name", item.get("vendor_name"))
        dest = vendor if name in ("73.jpg", "74.jpg") else relikd
        shutil.copyfile(site / item["site_path"], dest / name)
    return lp


def execute(lp):
    td = lp / "analysis/round19/T2"
    subprocess.run([sys.executable, "linemap.py"], cwd=td, check=True)
    subprocess.run([sys.executable, "probe.py", "--pages", "73,74", "--out", "out_probe_solved_fresh.json"], cwd=td, check=True)
    solved = read(td / "out_probe_solved_fresh.json")
    slots = sum(len(r["canon"]) for r in solved)
    matches = sum(sum(x == y for x, y in zip(r["canon"], r["best"])) for r in solved)
    if len(solved) != 10 or slots != 178 or matches / slots < .9:
        raise ValueError(f"Solved C1 gate failed: {matches}/{slots} in {len(solved)} lines")
    subprocess.run([sys.executable, "probe.py", "--out", "out_probe_fresh.json"], cwd=td, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--site-root", type=pathlib.Path, required=True)
    ap.add_argument("--artifact-root", type=pathlib.Path, help="Previously generated isolated liber-primus tree")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    source = args.source_root.resolve()
    site = args.site_root.resolve()
    plan = read(HERE / "plan.json")
    verify_inputs(plan, source, site)
    if args.rebuild:
        with tempfile.TemporaryDirectory(prefix="liberpedia-t2-") as temp:
            lp = build_tree(pathlib.Path(temp), plan, source, site)
            execute(lp)
            process(lp, source, args.check)
    elif args.artifact_root:
        process(args.artifact_root.resolve(), source, args.check)
    else:
        ap.error("Choose --rebuild or --artifact-root")


def process(lp, source, check):
    td = lp / "analysis/round19/T2"
    fresh = read(td / "out_probe_fresh.json")
    historical = read(source / "analysis/round19/T2/out_probe.json")
    rows = compact(fresh, historical)
    obj = {"schema": "liberpedia-t2-compact-lines-v1", "rows": rows}
    encoded = (json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if check:
        if encoded != (HERE / "line-results.json").read_bytes():
            raise ValueError("Compact line receipt differs from frozen output")
    else:
        (HERE / "line-results.json").write_bytes(encoded)
    print(f"T2 compact receipt: {len(rows)} lines; SHA256 {hashlib.sha256(encoded).hexdigest()}")


if __name__ == "__main__":
    main()
