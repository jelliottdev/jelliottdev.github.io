"""Independent checkpoint/merge and top-row check for pinned B04 Stage B.

This inspects the completed external work directory. It does not run the
1,385,600-candidate search or change its checkpoints.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
RUNNER = HERE.parent / "b04-2026-10-23" / "resumable.py"
spec = importlib.util.spec_from_file_location("b04_resumable", RUNNER)
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def verify(source, output, gate_path):
    H, S, ks, sk, hashes = R.load_source(source)
    inputs = R.stage_inputs("B", H, S, ks, sk)
    segs, entries, gens, reds, signs, atbs, dirs, offs = inputs
    man = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert man["manifest_sha256"] == R.digest({
        k: v for k, v in man.items() if k != "manifest_sha256"})
    assert man["source_revision"] == R.PIN and man["source_hashes"] == hashes
    assert man["stage"] == "B" and not man["synthetic"] and not man["g2_plant"]
    assert man["gate_receipt_sha256"] == R.sha(gate_path)
    assert man["segments"] == [{"name": name, "cipher_hex": bytes(cipher).hex()}
                               for name, cipher, _ in segs]
    assert man["entries"] == [{"label": label, "seed_hex": seed.hex()}
                              for label, seed in entries]
    assert (man["generators"], man["reductions"], man["signs"],
            man["atbash"], man["directions"], man["offsets"]) == (
                gens, reds, signs, atbs, dirs, offs)
    assert (man["beam_width"], man["max_skip"], man["topk"],
            man["chunk_seeds"]) == (H.BEAM_W, H.MAX_SKIP, 300, 4)
    assert man["histogram"] == [H.HIST_LO, H.HIST_HI, H.HIST_W, H.HIST_NB]
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    assert gate["G1_pass"] and gate["G2_pass"]
    assert gate["source_revision"] == R.PIN and gate["source_hashes"] == hashes
    assert gate["ordered_seed_manifest_sha256"] == R.digest([
        {"label": label, "seed_hex": seed.hex()} for label, seed in S.build()])

    ranges = R.chunk_ranges(len(entries), man["chunk_seeds"])
    per_seed = R.expected_per_seed(inputs)
    assert len(entries) == 504 and per_seed == 2560 and len(ranges) == 126
    bodies = [R.verify_chunk(output / f"chunk-{i:05d}.json", i, start, end,
                             man["manifest_sha256"], per_seed, man["topk"],
                             H.HIST_NB)
              for i, (start, end) in enumerate(ranges)]
    merged = json.loads((output / "merged.json").read_text(encoding="utf-8"))
    rebuilt = R.merge_chunks(bodies, man["topk"], H)
    assert all(merged[k] == rebuilt[k] for k in
               ("rows", "hist", "axis_best", "n_decodes"))
    assert merged["complete"] and merged["completed_chunks"] == len(ranges)
    assert merged["total_chunks"] == len(ranges)
    assert merged["n_decodes"] == merged["expected_decodes"] == 1_290_240
    assert sum(body["n_decodes"] for body in bodies) == merged["n_decodes"]
    assert [sum(body["hist"][i] for body in bodies) for i in range(H.HIST_NB)] == merged["hist"]
    for axis, score in merged["axis_best"].items():
        assert score == max(body["axis_best"].get(axis, -99) for body in bodies)
    assert len(merged["rows"]) == 300
    # A separate score-only ranking checks the merge's selection boundary.
    # Exact row order at an equal-score tie is still checked by R.merge_chunks.
    all_saved_scores = [row["score"] for body in bodies for row in body["rows"]]
    assert [row["score"] for row in merged["rows"]] == sorted(
        all_saved_scores, reverse=True)[:300]

    # Reconstruct the source worker's top decode outside the checkpoint merge.
    row = merged["rows"][0]
    assert row["segment"] == segs[0][0] and row["offset"] in offs
    assert row["label"] in {label for label, _ in entries}
    seed = bytes.fromhex(row["seed_hex"])
    assert (row["label"], seed) in entries
    nsym = max(offs) + max(len(s[1]) for s in segs) * (H.MAX_SKIP + 2) + 128
    raw = ks.make_bytes(row["gen"], seed, int(nsym * 1.35) + 256)
    base = ks.make_ks(row["gen"], row["red"], seed, nsym, raw=raw)
    key = base if row["dir"] == "fwd" else base[::-1]
    cipher = segs[0][1] if row["atbash"] == 0 else segs[0][2]
    direct = sk.beam_decode(cipher, key, sign=row["sign"], o=row["offset"],
                            beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    assert abs(direct["score"] - row["score"]) < 1e-12
    assert direct["translit"][:64] == row["head"]

    import sweep
    expected_summary = sweep.stage_summary("B", {**rebuilt, "elapsed_s": 1.0})
    expected_summary["elapsed_s"] = None
    expected_summary["rate_per_s"] = None
    assert merged["source_stage_summary"] == expected_summary
    return {"schema": "b04-stage-b-independent-check-v1",
            "source_revision": R.PIN,
            "manifest_sha256": man["manifest_sha256"],
            "manifest_file_sha256": R.sha(output / "manifest.json"),
            "gate_receipt_sha256": R.sha(gate_path),
            "merged_file_sha256": R.sha(output / "merged.json"),
            "source_head_cipher_sha256": hashlib.sha256(bytes(segs[0][1])).hexdigest(),
            "chunks_verified": len(bodies),
            "candidate_decodes": merged["n_decodes"],
            "histogram_count": sum(merged["hist"]),
            "top_row_source_score_direct": direct["score"],
            "top_row_source_head_direct": direct["translit"][:64],
            "full_chunk_merge_exact": True}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--gate-receipt", type=pathlib.Path, required=True)
    args = ap.parse_args()
    result = verify(args.source_root.resolve(), args.output.resolve(),
                    args.gate_receipt.resolve())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
