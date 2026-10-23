"""Re-run grouped T2 controls on the pinned fresh 229-class image instrument.

The source scripts are copied unchanged. Published raw outputs are checked by JSON
value because source json.dump newline formatting differs between platforms.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import hashlib
import os

HERE = pathlib.Path(__file__).resolve().parent
BASE = HERE.parent / "dukotah-t2-fresh-template-loo"
MORE = ("splice.py", "indel.py", "score_indel.py", "adj_indel.py", "separators.py", "sep19.py")
OUTPUTS = ("out_splice.json", "out_indel.json", "out_indel_score.json", "out_indel_adj.json", "out_separators.json", "out_sep19.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify(path, expected):
    if not path.is_file() or sha(path) != expected:
        raise ValueError(f"Missing or changed source/input: {path}")


def base_module():
    spec = importlib.util.spec_from_file_location("base_t2_replay", BASE / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cmd(td, name, *args):
    subprocess.run([sys.executable, name, *args], cwd=td, check=True)


def gate(td):
    x = read(td / "out_splice.json")
    dense = x["agg"]["dense-45-54"]
    if dense["n"] == 0 or dense["rec"] / dense["n"] < .5:
        raise ValueError(f"C2-prime dense recovery gate failed: {dense}")
    print(f"C2-prime gate passed: {dense['rec']}/{dense['n']} valid dense placements")


def compare(td):
    for name in OUTPUTS:
        if read(td / name) != read(HERE / name):
            raise ValueError(f"Source output differs from frozen record: {name}")
    print("Six T2 control outputs match frozen parsed receipts")


def run_controls(lp, source):
    td = lp / "analysis/round19/T2"
    for name in MORE:
        shutil.copyfile(source / "analysis/round19/T2" / name, td / name)
    geometry = lp / "analysis/geometry"
    geometry.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "analysis/geometry/separator_audit.json", geometry / "separator_audit.json")
    shutil.copyfile(td / "out_probe_fresh.json", td / "out_probe.json")
    run_cmd(td, "splice.py", "200")
    gate(td)
    run_cmd(td, "indel.py")
    run_cmd(td, "score_indel.py")
    run_cmd(td, "adj_indel.py")
    run_cmd(td, "separators.py")
    run_cmd(td, "sep19.py")
    return td


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--site-root", type=pathlib.Path, required=True)
    ap.add_argument("--artifact-root", type=pathlib.Path, help="Prior isolated fresh T2 liber-primus tree")
    ap.add_argument("--rebuild", action="store_true", help="Regenerate line map and probe, then all controls")
    ap.add_argument("--controls-only", action="store_true", help="Use bundled, hash-pinned fresh line map and probe")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if sum(bool(x) for x in (args.rebuild, args.controls_only, args.artifact_root)) != 1:
        ap.error("Choose exactly one of --rebuild, --controls-only or --artifact-root")
    plan = read(HERE / "plan.json")
    base = base_module()
    source = args.source_root.resolve()
    site = args.site_root.resolve()
    verify(BASE / "plan.json", plan["input_plan_sha256"])
    base.verify_inputs(read(BASE / "plan.json"), source, site)
    for rel, digest in plan["source_sha256"].items():
        verify(source / rel, digest)
    if args.rebuild or args.controls_only:
        with tempfile.TemporaryDirectory(prefix="liberpedia-t2-controls-") as temp:
            lp = base.build_tree(pathlib.Path(temp), read(BASE / "plan.json"), source, site)
            if args.rebuild:
                base.execute(lp)
            else:
                td = lp / "analysis/round19/T2"
                for name, digest in (("out_linemap.json", plan["fresh_line_map_sha256"]),
                                     ("out_probe_fresh.json", plan["fresh_probe_sha256"])):
                    verify(HERE / name, digest)
                    shutil.copyfile(HERE / name, td / name)
                if os.sep == "/":
                    # The pinned receipt was generated on Windows. Only filesystem
                    # separators change; all mapped rows/positions remain fixed.
                    line_map = read(td / "out_linemap.json")
                    for row in line_map["map"]:
                        row["path"] = row["path"].replace("\\", "/")
                    (td / "out_linemap.json").write_text(json.dumps(line_map), encoding="utf-8")
            td = run_controls(lp, source)
            if args.check:
                compare(td)
    else:
        lp = args.artifact_root.resolve()
        td = lp / "analysis/round19/T2"
        verify(td / "out_linemap.json", plan["fresh_line_map_sha256"])
        verify(td / "out_probe_fresh.json", plan["fresh_probe_sha256"])
        if args.check:
            gate(td)
            compare(td)


if __name__ == "__main__":
    main()
