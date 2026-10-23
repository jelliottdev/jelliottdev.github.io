"""Check this bundle, or rerun its pinned B04 source grid into an external folder.

Usage:
  python experiments/records/dukotah-b04-full-source-replay/run.py --check
  python experiments/records/dukotah-b04-full-source-replay/run.py --quick
  python experiments/records/dukotah-b04-full-source-replay/run.py --full --output DIR

The --full campaign takes many minutes. It never writes into the bundled source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ABC = HERE / "replay/b04-2026-10-23/resumable.py"
D = HERE / "replay/b04-stage-b-2026-10-23/resumable_d.py"
SRC = HERE / "source"


def call(args):
    subprocess.run([sys.executable, *map(str, args)], check=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_loader_check():
    # The portable adapter checks every original executable/input hash against
    # results.json. No network or Git metadata is needed.
    import importlib.util
    spec = importlib.util.spec_from_file_location("b04_portable", ABC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    H, S, ks, sk, hashes = module.load_source(SRC)
    assert len(hashes) == 19 and H.HEAD_L == 120 and H.PAGE_L == 100
    assert len(module.stage_inputs("A", H, S, ks, sk)[1]) == 2165
    return module


def quick():
    source_loader_check()
    with tempfile.TemporaryDirectory(prefix="b04-quick-") as dirname:
        out = pathlib.Path(dirname) / "synthetic-A"
        call([ABC, "--source-root", SRC, "--stage", "A", "--synthetic",
              "--output", out, "--nproc", 1, "--chunk-seeds", 1])
        data = json.loads((out / "merged.json").read_text(encoding="utf-8"))
        assert data["complete"] and data["n_decodes"] == data["expected_decodes"] == 1280
    print("portable source bytes and 1,280 synthetic decodes: PASS")


def full(out: pathlib.Path, workers: int):
    source_loader_check()
    from check import check
    check()  # Fail closed on an altered archived gate or source input.
    out = out.resolve()
    if out == HERE or HERE in out.parents:
        raise ValueError("full checkpoints must live outside the downloadable bundle")
    out.mkdir(parents=True, exist_ok=True)
    gate = HERE / "replay/G2-gate.json"
    # Re-execute the full planted G2 grid before the manuscript grid. The
    # archived G1/G2 gate is byte- and seed-manifest-bound in the wrapper.
    g2 = out / "G2"
    call([ABC, "--source-root", SRC, "--stage", "A", "--g2-plant",
          "--output", g2, "--nproc", workers, "--chunk-seeds", 4])
    planted = json.loads((g2 / "merged.json").read_text(encoding="utf-8"))["g2_gate"]
    if not planted["passed"] or planted["planted_rank_in_topk"] != 1:
        raise RuntimeError("planted full-grid G2 control failed; stopping before LP2")
    print("G2 planted ranking PASS; starting LP2 stages A/B/C", flush=True)
    for stage, width in (("A", 4), ("B", 4), ("C", 1)):
        target = out / stage
        call([ABC, "--source-root", SRC, "--stage", stage,
              "--output", target, "--nproc", workers, "--chunk-seeds", width,
              "--topk", 300, "--allow-full", "--gate-receipt", gate])
        merged = json.loads((target / "merged.json").read_text(encoding="utf-8"))
        archived = json.loads((HERE / f"replay/results_{stage}.json").read_text(encoding="utf-8"))
        for field in ("n_decodes", "expected_decodes", "hist", "axis_best"):
            if merged[field] != archived[field]:
                raise RuntimeError(f"Stage {stage} source result differs: {field}")
        # Stage D's source gate binds independently checked prior files. The
        # new merged byte hash differs in its elapsed-time field, so produce a
        # fresh, explicitly scoped checkpoint receipt for this fresh run.
        receipt = {
            "source_revision": "f08b20b632d91209ddbaa747e8e2f23df0c78ba1",
            "manifest_sha256": merged["manifest_sha256"],
            "merged_file_sha256": sha(target / "merged.json"),
            "full_chunk_merge_exact": True,
            "scope": "resumable wrapper's per-chunk SHA verification and complete source merge",
        }
        (target / "check.json").write_text(json.dumps(receipt, sort_keys=True) + "\n",
                                           encoding="utf-8", newline="\n")
        print(f"Stage {stage} complete: {merged['n_decodes']:,} decodes", flush=True)
    call([D, "--source-root", SRC, "--output", out / "D", "--nproc", workers,
          "--allow-full", "--decoder-backend", "prefix_shared",
          "--prior-a", out / "A/merged.json", "--prior-b", out / "B/merged.json",
          "--prior-c", out / "C/merged.json",
          "--prior-a-check", out / "A/check.json", "--prior-b-check", out / "B/check.json",
          "--prior-c-check", out / "C/check.json"])
    print("Full source-defined campaign complete. Compare output summaries with results.json.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--quick", action="store_true")
    group.add_argument("--full", action="store_true")
    ap.add_argument("--output", type=pathlib.Path)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.workers < 1:
        ap.error("--workers must be positive")
    if args.full:
        if args.output is None:
            ap.error("--full requires --output outside this bundle")
        full(args.output, args.workers)
    elif args.quick:
        quick()
    else:
        from check import check
        print(json.dumps(check(), sort_keys=True))


if __name__ == "__main__":
    main()
