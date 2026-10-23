"""Synthetic parity and restart tests for resumable.py; no LP2 sweep."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b04_resumable", HERE / "resumable.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def invoke(root, stage, output, nproc, max_chunks=None):
    cmd = [sys.executable, str(HERE / "resumable.py"), "--source-root", str(root),
           "--stage", stage, "--output", str(output), "--synthetic",
           "--nproc", str(nproc), "--chunk-seeds", "1", "--topk", "5"]
    if max_chunks is not None:
        cmd += ["--max-chunks", str(max_chunks)]
    return subprocess.run(cmd, capture_output=True, text=True, check=True)


def core(result):
    return {k: result[k] for k in ("rows", "hist", "axis_best", "n_decodes")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, default=HERE / "resumable-test-receipt.json")
    args = ap.parse_args()
    source = args.source_root.resolve()
    H, S, ks, sk, hashes = R.load_source(source)
    import control
    g2 = R.stage_inputs("A", H, S, ks, sk, g2_plant=True)
    g2_segs, g2_entries = g2[0], g2[1]
    assert len(g2_entries) == 2165 and len(g2_segs[0][1]) == 120
    assert R.expected_per_seed(g2) * len(g2_entries) == 1_385_600
    assert R.digest([{"label": label, "seed_hex": seed.hex()}
                     for label, seed in g2_entries]) == "0709571f26fe003e97936f9edc559dabeae6f1a55ea1ef91aa11b6bb32d93d03"
    plant_entry = next(e for e in g2_entries if e[1] == control.PLANT_SEED)
    H._init(g2_segs, *g2[2:], 300)
    planted_rows = H._work([plant_entry])[0]
    planted = next(row for row in planted_rows
                   if row[2] == control.PLANT_SEED and row[3:8] ==
                   (control.PLANT_GEN, control.PLANT_RED, control.PLANT_SIGN,
                    control.PLANT_ATBASH, control.PLANT_DIR))
    assert planted[0] >= -5.5
    rows = []
    with tempfile.TemporaryDirectory(prefix="b04-checkpoint-test-") as tmp:
        base = pathlib.Path(tmp)
        for stage in "ABC":
            segs, entries, gens, reds, signs, atbs, dirs, offs = R.stage_inputs(stage, H, S, ks, sk, True)
            source_result = H.run_stage(segs, entries, gens=gens, reds=reds, signs=signs,
                                        atbs=atbs, dirs=dirs, offs=offs, topk=5,
                                        nproc=1, chunk_seeds=1, label=f"parity-{stage}")
            for nproc in (1, 2):
                output = base / f"{stage}-{nproc}"
                if stage == "A":
                    invoke(source, stage, output, nproc, max_chunks=1)
                    partial = json.loads((output / "chunk-00000.json").read_text(encoding="utf-8"))
                    assert not (output / "merged.json").exists()
                    saved_hash = R.sha(output / "chunk-00000.json")
                    invoke(source, stage, output, nproc)
                    assert R.sha(output / "chunk-00000.json") == saved_hash
                    assert R.digest(partial["payload"]) == partial["payload_sha256"]
                else:
                    invoke(source, stage, output, nproc)
                merged = json.loads((output / "merged.json").read_text(encoding="utf-8"))
                assert merged["complete"] and merged["n_decodes"] == merged["expected_decodes"]
                assert core(merged) == core(source_result), f"{stage} {nproc} source mismatch"
                import sweep
                expected_summary = sweep.stage_summary(stage, source_result)
                actual_summary = merged["source_stage_summary"]
                for field in ("stage", "n_decodes", "best_score", "bar", "hit",
                              "over_bar", "top50", "hist", "hist_stats", "axis_best"):
                    assert actual_summary[field] == expected_summary[field], (stage, nproc, field)
                rows.append({"stage": stage, "processes": nproc,
                             "n_decodes": merged["n_decodes"],
                             "source_exact_aggregate_match": True,
                             "top_rows_sha256": R.digest(merged["rows"]),
                             "hist_sha256": R.digest(merged["hist"])})
        # A complete chunk with altered content cannot be silently skipped.
        path = base / "A-1" / "chunk-00000.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["payload"]["n_decodes"] -= 1
        R.atomic_json(path, data)
        bad = subprocess.run([sys.executable, str(HERE / "resumable.py"),
                              "--source-root", str(source), "--stage", "A", "--output",
                              str(base / "A-1"), "--synthetic", "--topk", "5"],
                             capture_output=True, text=True)
        assert bad.returncode != 0 and "corrupted chunk hash" in bad.stderr
    receipt = {"schema": "b04-resumable-synthetic-parity-v1",
               "source_revision": R.PIN, "source_hashes": hashes,
               "rows": rows, "restart_one_chunk_preserved": True,
               "altered_chunk_rejected": True,
               "g2_source_control": {"ordered_seed_manifest_sha256": R.digest([
                   {"label": label, "seed_hex": seed.hex()} for label, seed in g2_entries]),
                   "cipher_sha256": hashlib.sha256(bytes(g2_segs[0][1])).hexdigest(),
                   "planted_single_seed_score": planted[0],
                   "single_seed_passes_source_bar": planted[0] >= -5.5,
                   "full_grid_not_run_in_test": True},
               "scope": "Synthetic ciphertext only; complete A/B/C axes with two synthetic seeds and 55 synthetic page segments for C. No LP2 manuscript sweep."}
    R.atomic_json(args.output, receipt)
    print(json.dumps({"checks": len(rows), "restart": True, "tamper_rejected": True}))


if __name__ == "__main__":
    main()
