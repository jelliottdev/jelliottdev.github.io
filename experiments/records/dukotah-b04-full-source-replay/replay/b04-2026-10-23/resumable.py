"""Checkpointed B04 A/B/C wrapper. Calls the pinned source worker unchanged.

This is an internal execution tool, not a modified decoder or a manuscript result.
Full LP2 runs require --allow-full and a previously passing source control receipt.
"""
import argparse
import hashlib
import heapq
import json
import os
import pathlib
import sys
import tempfile
import time
from multiprocessing import Pool

PIN = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
SOURCE_FILES = (
    "analysis/round13/B04/harness.py", "analysis/round13/B04/sweep.py",
    "analysis/round13/B04/ks.py", "analysis/round13/B04/seeds.py",
    "analysis/round13/B04/control.py",
    "analysis/campaign18_skip/skipdecode.py", "analysis/round11/lib_numchannel.py",
    "src/lp/score.py", "data/english_quadgrams.txt",
    "data/krisyotam_runes.txt", "analysis/run_stats.py", "src/lp/gematria.py",
    "data/keys/thematic.txt", "data/keys/armada18/cicada_koans_and_lp_sections.txt",
    "data/keys/armada18/cicada_2012_2013_puzzle_texts.txt",
    "data/keys/armada18/cicada_pgp_messages.txt",
    "analysis/pp49_51/canon_256.bin", "analysis/pp49_51/canon_256_decpref.bin",
    "data/keys/self_reliance.txt",
)
_WORK_H = None


def _init_source_worker(b04_path, segs, gens, reds, signs, atbs, dirs, offs, topk):
    global _WORK_H
    sys.path.insert(0, b04_path)
    import harness
    _WORK_H = harness
    _WORK_H._init(segs, gens, reds, signs, atbs, dirs, offs, topk)


def _work_indexed(item):
    index, start, end, entries = item
    return index, start, end, _WORK_H._work(entries)


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(obj):
    return hashlib.sha256(canonical(obj)).hexdigest()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent,
                                     prefix=".b04-", suffix=".tmp", delete=False) as f:
        tmp = pathlib.Path(f.name)
        json.dump(obj, f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_source(source):
    expected = json.loads((pathlib.Path(__file__).resolve().parents[2] / "results.json")
                          .read_text(encoding="utf-8"))
    if expected["source_revision"] != PIN:
        raise ValueError("bundle source revision mismatch")
    root = source / "liber-primus"
    hashes = {p: sha(root / p) for p in SOURCE_FILES}
    for path, actual in hashes.items():
        if expected["source_file_sha256"].get(path) != actual:
            raise ValueError(f"bundled source differs from pinned bytes: {path}")
    b04 = root / "analysis/round13/B04"
    sys.path.insert(0, str(b04))
    import harness as H
    import seeds as S
    import ks
    import skipdecode as sk
    return H, S, ks, sk, hashes


def stage_inputs(stage, H, S, ks, sk, synthetic=False, g2_plant=False):
    if g2_plant:
        if stage != "A" or synthetic:
            raise ValueError("G2 plant uses only the complete source Stage-A axes")
        import control
        plain = sk.eng_to_idx(control.PLAIN)[:H.HEAD_L]
        key = ks.make_ks(control.PLANT_GEN, control.PLANT_RED, control.PLANT_SEED,
                         H.HEAD_L * (H.MAX_SKIP + 2) + 128)
        cipher, _, _ = sk.encipher_keyskip(plain, key, sign=control.PLANT_SIGN,
                                          supp=.83, seed=3301)
        return ([H.make_segment("plant", cipher)], S.build(), list(ks.GEN_NAMES),
                list(ks.RED_NAMES), [-1, 1], [0, 1], ["fwd", "rev"], [0])
    if synthetic:
        import math
        text = "THE PRIMES ARE SACRED AND THE PILGRIM SEEKS THE TRUTH "
        unit = sk.eng_to_idx(text)
        plain = (unit * math.ceil(120 / len(unit)))[:120]
        key = ks.make_ks("sha256_ctr", "mod29", b"UNSEARCHED SYNTHETIC KEY", 512)
        cipher, _, _ = sk.encipher_keyskip(plain, key, sign=-1, supp=.83, seed=3301)
        entries = [("synthetic01", b"SYNTHETIC B04 SEED ONE"),
                   ("synthetic02", b"SYNTHETIC B04 SEED TWO")]
        head = [H.make_segment("synthetic-head", cipher)]
        pages = [H.make_segment(f"synthetic-page-{i:02d}",
                                cipher[(i % 20):(i % 20) + 100]) for i in range(55)]
    else:
        entries = S.build()
        head = [H.head_segment()]
        pages = H.page_segments()
    if stage == "A":
        return head, entries, list(ks.GEN_NAMES), list(ks.RED_NAMES), [-1, 1], [0, 1], ["fwd", "rev"], [0]
    core = entries if synthetic else S.core(entries)
    if stage == "B":
        return head, core, list(ks.GEN_NAMES), ["mod29", "rej29"], [-1, 1], [0, 1], ["fwd", "rev"], [1, 4, 16, 29, 64, 128, 256, 512, 1024, 3301]
    if stage == "C":
        return pages, core, list(ks.GEN_NAMES), ["mod29", "rej29"], [-1, 1], [0, 1], ["fwd"], [0]
    raise ValueError(stage)


def manifest(stage, args, inputs, hashes, H):
    segs, entries, gens, reds, signs, atbs, dirs, offs = inputs
    m = {"schema": "b04-chunk-manifest-v1", "source_revision": PIN,
         "source_hashes": hashes, "stage": stage, "synthetic": args.synthetic,
         "g2_plant": args.g2_plant,
         "segments": [{"name": n, "cipher_hex": bytes(c).hex()} for n, c, _ in segs],
         "entries": [{"label": n, "seed_hex": s.hex()} for n, s in entries],
         "generators": gens, "reductions": reds, "signs": signs, "atbash": atbs,
         "directions": dirs, "offsets": offs, "beam_width": H.BEAM_W,
         "max_skip": H.MAX_SKIP, "topk": args.topk, "chunk_seeds": args.chunk_seeds,
         "histogram": [H.HIST_LO, H.HIST_HI, H.HIST_W, H.HIST_NB]}
    if args.gate_receipt:
        m["gate_receipt_sha256"] = sha(args.gate_receipt)
    m["manifest_sha256"] = digest(m)
    return m


def chunk_ranges(n, width):
    return [(i, min(i + width, n)) for i in range(0, n, width)]


def expected_per_seed(inputs):
    segs, _, gens, reds, signs, atbs, dirs, offs = inputs
    return len(segs) * len(gens) * len(reds) * len(signs) * len(atbs) * len(dirs) * len(offs)


def pack_chunk(index, start, end, raw, man_hash, H):
    rows, hist, axis, count = raw
    body = {"schema": "b04-complete-chunk-v1", "manifest_sha256": man_hash,
            "index": index, "seed_start": start, "seed_end": end,
            "rows": [H._row_dict(row) for row in rows], "hist": hist,
            "axis_best": {f"{a}|{b}": v for (a, b), v in axis.items()},
            "n_decodes": count}
    return {"payload": body, "payload_sha256": digest(body)}


def verify_chunk(path, index, start, end, man_hash, per_seed, topk, hist_n):
    envelope = json.loads(path.read_text(encoding="utf-8"))
    body = envelope["payload"]
    if digest(body) != envelope["payload_sha256"]:
        raise ValueError(f"corrupted chunk hash: {path}")
    if (body["schema"] != "b04-complete-chunk-v1" or
        body["manifest_sha256"] != man_hash or body["index"] != index or
        body["seed_start"] != start or body["seed_end"] != end or
        body["n_decodes"] != (end - start) * per_seed or
        len(body["hist"]) != hist_n or len(body["rows"]) > topk or
        any(not isinstance(v, int) or v < 0 for v in body["hist"]) or
        sum(body["hist"]) > body["n_decodes"]):
        raise ValueError(f"invalid chunk metadata: {path}")
    return body


def row_tuple(d):
    return (d["score"], d["label"], bytes.fromhex(d["seed_hex"]), d["gen"],
            d["red"], d["sign"], d["atbash"], d["dir"], d["offset"],
            d["segment"], d["head"])


def merge_chunks(bodies, topk, H):
    heap, hist, axis, count = [], [0] * H.HIST_NB, {}, 0
    for body in bodies:
        count += body["n_decodes"]
        for row in body["rows"]:
            tup = row_tuple(row)
            if len(heap) < topk:
                heapq.heappush(heap, tup)
            elif tup[0] > heap[0][0]:
                heapq.heapreplace(heap, tup)
        for i, value in enumerate(body["hist"]):
            hist[i] += value
        for key, value in body["axis_best"].items():
            axis[key] = max(axis.get(key, -99), value)
    return {"rows": [H._row_dict(r) for r in sorted(heap, key=lambda r: -r[0])],
            "hist": hist, "axis_best": axis, "n_decodes": count}


def execute(args):
    if not args.synthetic and not args.g2_plant and not args.allow_full:
        raise ValueError("full LP2 run disabled; use --allow-full with verified control receipt")
    H, S, ks, sk, hashes = load_source(args.source_root.resolve())
    inputs = stage_inputs(args.stage, H, S, ks, sk, args.synthetic, args.g2_plant)
    segs, entries, gens, reds, signs, atbs, dirs, offs = inputs
    if not args.synthetic and not args.g2_plant:
        if args.gate_receipt is None:
            raise ValueError("full run requires a current G1/G2 passing gate receipt")
        gate = json.loads(args.gate_receipt.read_text(encoding="utf-8"))
        current_entries = [{"label": n, "seed_hex": s.hex()} for n, s in S.build()]
        if (gate.get("source_revision") != PIN or not gate.get("G1_pass") or
            not gate.get("G2_pass") or gate.get("source_hashes") != hashes or
            gate.get("ordered_seed_manifest_sha256") != digest(current_entries) or
            gate.get("g2_cipher_sha256") != hashlib.sha256(bytes(stage_inputs(
                "A", H, S, ks, sk, g2_plant=True)[0][0][1])).hexdigest()):
            raise ValueError("full run requires pinned passing G1/G2 and matching source, seed and plant hashes")
    man = manifest(args.stage, args, inputs, hashes, H)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    mp = output / "manifest.json"
    if mp.exists():
        saved = json.loads(mp.read_text(encoding="utf-8"))
        if saved != man or saved["manifest_sha256"] != digest({k: v for k, v in saved.items() if k != "manifest_sha256"}):
            raise ValueError("manifest changed; use a different output directory")
    else:
        if any(output.iterdir()):
            raise ValueError("nonempty output directory without a manifest")
        atomic_json(mp, man)
    ranges = chunk_ranges(len(entries), args.chunk_seeds)
    pending = []
    for i, (start, end) in enumerate(ranges):
        path = output / f"chunk-{i:05d}.json"
        if path.exists():
            verify_chunk(path, i, start, end, man["manifest_sha256"],
                         expected_per_seed(inputs), args.topk, H.HIST_NB)
        else:
            pending.append((i, start, end, entries[start:end]))
    selected = pending if args.max_chunks is None else pending[:args.max_chunks]
    completed_this_run = 0
    t0 = time.monotonic()
    if args.nproc == 1:
        H._init(segs, gens, reds, signs, atbs, dirs, offs, args.topk)
        stream = ((i, start, end, H._work(batch)) for i, start, end, batch in selected)
        for i, start, end, raw in stream:
            chunk = pack_chunk(i, start, end, raw, man["manifest_sha256"], H)
            if chunk["payload"]["n_decodes"] != (end-start)*expected_per_seed(inputs):
                raise ValueError("source worker returned incomplete chunk")
            atomic_json(output / f"chunk-{i:05d}.json", chunk)
            completed_this_run += 1
            if completed_this_run % 20 == 0:
                print(f"{completed_this_run}/{len(selected)} new chunks saved", flush=True)
    else:
        b04_path = str(args.source_root.resolve() / "liber-primus/analysis/round13/B04")
        with Pool(args.nproc, initializer=_init_source_worker,
                  initargs=(b04_path, segs, gens, reds, signs, atbs, dirs, offs, args.topk)) as pool:
            for i, start, end, raw in pool.imap_unordered(_work_indexed, selected):
                chunk = pack_chunk(i, start, end, raw, man["manifest_sha256"], H)
                if chunk["payload"]["n_decodes"] != (end-start)*expected_per_seed(inputs):
                    raise ValueError("source worker returned incomplete chunk")
                atomic_json(output / f"chunk-{i:05d}.json", chunk)
                completed_this_run += 1
                if completed_this_run % 20 == 0:
                    print(f"{completed_this_run}/{len(selected)} new chunks saved", flush=True)
    bodies = []
    for i, (start, end) in enumerate(ranges):
        path = output / f"chunk-{i:05d}.json"
        if path.exists():
            bodies.append(verify_chunk(path, i, start, end, man["manifest_sha256"],
                                        expected_per_seed(inputs), args.topk, H.HIST_NB))
    complete = len(bodies) == len(ranges)
    result = merge_chunks(bodies, args.topk, H)
    result.update({"schema": "b04-resumable-stage-v1", "stage": args.stage,
                   "manifest_sha256": man["manifest_sha256"], "complete": complete,
                   "completed_chunks": len(bodies), "total_chunks": len(ranges),
                   "expected_decodes": expected_per_seed(inputs)*len(entries),
                   "elapsed_this_invocation_s": time.monotonic()-t0})
    if complete:
        import sweep
        source_format = dict(result)
        # Resume can span sessions and workers; a source-style wall time/rate
        # cannot be reconstructed from finished chunks.
        source_format["elapsed_s"] = 1.0
        result["source_stage_summary"] = sweep.stage_summary(args.stage, source_format)
        result["source_stage_summary"]["elapsed_s"] = None
        result["source_stage_summary"]["rate_per_s"] = None
        if args.g2_plant:
            import control
            truth = (control.PLANT_SEED.hex(), control.PLANT_GEN, control.PLANT_RED,
                     control.PLANT_SIGN, control.PLANT_ATBASH, control.PLANT_DIR)
            rank, match = None, None
            for i, row in enumerate(result["rows"], 1):
                if (row["seed_hex"], row["gen"], row["red"], row["sign"],
                    row["atbash"], row["dir"]) == truth:
                    rank, match = i, row
                    break
            result["g2_gate"] = {"planted_rank_in_topk": rank,
                                 "planted_score": match["score"] if match else None,
                                 "source_bar": -5.5,
                                 "passed": rank == 1 and match["score"] >= -5.5 if match else False,
                                 "planted_tuple": truth}
            if args.g1_preflight:
                pre = json.loads(args.g1_preflight.read_text(encoding="utf-8"))
                expected_files = pre.get("source_files", {})
                matched = bool(expected_files) and all(
                    sha(args.source_root.resolve() / path) == expected_hash
                    for path, expected_hash in expected_files.items())
                g1_pass = (pre.get("source_revision") == PIN and matched and
                           pre.get("g1_current_code_pass") is True and
                           pre.get("full_message", {}).get("full_message_gate_pass") is True)
                receipt = {"schema": "b04-fresh-g1-g2-gate-v1", "source_revision": PIN,
                           "source_hashes": hashes,
                           "ordered_seed_manifest_sha256": digest(man["entries"]),
                           "g2_cipher_sha256": hashlib.sha256(bytes(segs[0][1])).hexdigest(),
                           "g1_preflight_sha256": sha(args.g1_preflight),
                           "G1_pass": g1_pass,
                           "G2_pass": result["g2_gate"]["passed"],
                           "g2_rank": rank, "g2_score": match["score"] if match else None,
                           "g2_config_count": result["n_decodes"],
                           "g2_manifest_sha256": man["manifest_sha256"]}
                atomic_json(output / "gate-receipt.json", receipt)
        atomic_json(output / "merged.json", result)
    print(json.dumps({k: result[k] for k in ("stage", "complete", "completed_chunks",
                                       "total_chunks", "n_decodes", "expected_decodes")}), flush=True)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--stage", choices="ABC", required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--g2-plant", action="store_true", help="Full source G2 planted gate; no LP2 input")
    ap.add_argument("--allow-full", action="store_true")
    ap.add_argument("--gate-receipt", type=pathlib.Path)
    ap.add_argument("--g1-preflight", type=pathlib.Path,
                    help="Pinned passing G1 receipt to bind into a completed G2 receipt")
    ap.add_argument("--nproc", type=int, default=1)
    ap.add_argument("--chunk-seeds", type=int, default=1)
    ap.add_argument("--topk", type=int, default=300)
    ap.add_argument("--max-chunks", type=int)
    arguments = ap.parse_args()
    if arguments.chunk_seeds < 1 or arguments.nproc < 1 or arguments.topk < 1:
        ap.error("nproc, chunk-seeds and topk must be positive")
    if arguments.synthetic and arguments.g2_plant:
        ap.error("synthetic microbenchmark and source G2 are exclusive")
    execute(arguments)
