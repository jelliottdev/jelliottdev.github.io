"""Independently reconstruct a completed B04 control.py G2 checkpoint merge."""
import argparse
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("b04_resumable", HERE / "resumable.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)


def verify(source, output):
    H, S, ks, sk, hashes = R.load_source(source)
    import control
    man = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert man["manifest_sha256"] == R.digest({k: v for k, v in man.items()
                                                 if k != "manifest_sha256"})
    assert man["source_revision"] == R.PIN and man["source_hashes"] == hashes
    assert man["stage"] == "A" and man["g2_plant"] and not man["synthetic"]
    inputs = R.stage_inputs("A", H, S, ks, sk, g2_plant=True)
    segs, entries = inputs[:2]
    assert man["entries"] == [{"label": label, "seed_hex": seed.hex()}
                              for label, seed in entries]
    assert man["segments"] == [{"name": name, "cipher_hex": bytes(cipher).hex()}
                                for name, cipher, _ in segs]
    ranges = R.chunk_ranges(len(entries), man["chunk_seeds"])
    bodies = [R.verify_chunk(output / f"chunk-{i:05d}.json", i, start, end,
                              man["manifest_sha256"], R.expected_per_seed(inputs),
                              man["topk"], H.HIST_NB)
              for i, (start, end) in enumerate(ranges)]
    merged = json.loads((output / "merged.json").read_text(encoding="utf-8"))
    independent = R.merge_chunks(bodies, man["topk"], H)
    assert all(merged[key] == independent[key]
               for key in ("rows", "hist", "axis_best", "n_decodes"))
    assert merged["n_decodes"] == 1_385_600 and merged["complete"]
    plant = (control.PLANT_SEED.hex(), control.PLANT_GEN, control.PLANT_RED,
             control.PLANT_SIGN, control.PLANT_ATBASH, control.PLANT_DIR)
    ranks = [i for i, row in enumerate(independent["rows"], 1)
             if (row["seed_hex"], row["gen"], row["red"], row["sign"],
                 row["atbash"], row["dir"]) == plant]
    assert merged["g2_gate"]["planted_rank_in_topk"] == (ranks[0] if ranks else None)
    key = ks.make_ks(control.PLANT_GEN, control.PLANT_RED, control.PLANT_SEED,
                     H.HEAD_L * (H.MAX_SKIP + 2) + 128)
    direct = sk.beam_decode(segs[0][1], key, sign=control.PLANT_SIGN, o=0,
                            beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    if ranks:
        assert abs(independent["rows"][ranks[0]-1]["score"]-direct["score"]) < 1e-12
    gate = json.loads((output / "gate-receipt.json").read_text(encoding="utf-8"))
    assert gate["source_hashes"] == hashes
    assert gate["ordered_seed_manifest_sha256"] == R.digest(man["entries"])
    assert gate["g2_cipher_sha256"] == hashlib.sha256(bytes(segs[0][1])).hexdigest()
    assert gate["g2_manifest_sha256"] == man["manifest_sha256"]
    assert gate["G2_pass"] == (bool(ranks) and ranks[0] == 1 and direct["score"] >= -5.5)
    receipt = {"schema": "b04-g2-independent-check-v1", "source_revision": R.PIN,
               "manifest_sha256": man["manifest_sha256"],
               "ordered_seed_manifest_sha256": R.digest(man["entries"]),
               "cipher_sha256": gate["g2_cipher_sha256"],
               "chunks_verified": len(bodies), "candidate_decodes": merged["n_decodes"],
               "source_plant_score_direct": direct["score"],
               "plant_rank": ranks[0] if ranks else None, "G2_pass": gate["G2_pass"],
               "full_chunk_merge_exact": True}
    R.atomic_json(output / "independent-check.json", receipt)
    return receipt


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    args = ap.parse_args()
    print(json.dumps(verify(args.source_root.resolve(), args.output.resolve())))
