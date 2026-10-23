"""Checkpointed B04 Stage D, with an exact-source key-padding read audit.

The source decoder, score, key generator and A/B/C top50 tuple rule are unchanged.
Synthetic short-input tests are supported; a real run additionally requires three
completed prior stage summaries and --allow-full. No real Stage D has been run.
"""
import argparse
import importlib.util
import json
import pathlib
import time
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "b04_resumable", HERE.parent / "b04-2026-10-23" / "resumable.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)
_D_WORK = {}


def _init_d_worker(source_root, segments, picks):
    H, _, ks, sk, _ = R.load_source(pathlib.Path(source_root))
    _D_WORK.update(H=H, ks=ks, sk=sk, segments=segments, picks=picks)


def _work_d_indexed(index):
    si, pi = index
    value, audit = decode_cell(_D_WORK["picks"][pi],
                               _D_WORK["segments"][si],
                               _D_WORK["H"], _D_WORK["ks"], _D_WORK["sk"])
    return si, pi, value, audit


class ObservedKey(list):
    """A list with identical values that counts reads of source-added zeros."""

    def __init__(self, values, native_length, reads=None):
        super().__init__(values)
        self.native_length = native_length
        self.reads = reads if reads is not None else {
            "read_count": 0, "max_read_index": -1, "padded_read_count": 0,
            "extension_count": 0}

    def __add__(self, other):
        self.reads["extension_count"] += 1
        return ObservedKey(list.__add__(self, other), self.native_length,
                           self.reads)

    def __getitem__(self, item):
        if isinstance(item, int):
            self.reads["read_count"] += 1
            self.reads["max_read_index"] = max(self.reads["max_read_index"], item)
            if item >= self.native_length:
                self.reads["padded_read_count"] += 1
        return list.__getitem__(self, item)


def select_picks(priors):
    """Literal sweep.stage_d stable concat/sort/dedup of A, B, C top50 rows."""
    rows = []
    for stage in priors:
        rows.extend(stage.get("top50", []))
    rows.sort(key=lambda d: -d["score"])
    seen, picks = set(), []
    for row in rows:
        key = (row.get("seed_hex"), row.get("gen"), row.get("red"),
               row.get("sign"), row.get("atbash"), row.get("dir"),
               row.get("offset"))
        if key in seen:
            continue
        seen.add(key)
        picks.append(row)
        if len(picks) >= 300:
            break
    return picks


def load_priors(paths, check_paths):
    priors = []
    hashes = {}
    for stage, path, check_path in zip("ABC", paths, check_paths):
        data = json.loads(path.read_text(encoding="utf-8"))
        checked = json.loads(check_path.read_text(encoding="utf-8"))
        if (data.get("stage") != stage or not data.get("complete") or
            data.get("n_decodes") != data.get("expected_decodes") or
            data.get("source_stage_summary", {}).get("stage") != stage or
            checked.get("source_revision") != R.PIN or
            checked.get("manifest_sha256") != data.get("manifest_sha256") or
            checked.get("merged_file_sha256") != R.sha(path) or
            checked.get("full_chunk_merge_exact") is not True):
            raise ValueError(f"incomplete or wrong prior Stage {stage}: {path}")
        priors.append(data["source_stage_summary"])
        hashes[stage] = R.sha(path)
        hashes[f"{stage}_independent_check"] = R.sha(check_path)
    return priors, hashes


def synthetic_inputs(H, sk):
    # Short, controlled transcripts exercise checkpointing without LP2 Stage D.
    seed = b"THE PRIMES ARE SACRED"
    base = {"seed": seed.decode(), "seed_hex": seed.hex(),
            "gen": "sha256_ctr", "red": "mod29", "sign": -1,
            "atbash": 0, "dir": "fwd", "offset": 0}
    alternate = {**base, "gen": "sha512_ctr", "score": -6.1}
    first = {**base, "score": -5.9}
    duplicate = {**base, "score": -6.3}
    priors = [{"top50": [first]}, {"top50": [alternate]},
              {"top50": [duplicate]}]
    c = sk.eng_to_idx("THEPRIMESARESACREDANDTHEPILGRIMSEEKS")
    segments = [H.make_segment("synthetic-short-a", c[:10]),
                H.make_segment("synthetic-short-b", c[:16])]
    return priors, segments


def make_manifest(H, hashes, priors, prior_hashes, segments, synthetic):
    picks = select_picks(priors)
    if len(picks) > 150:
        raise ValueError("more than three source top50 lists supplied")
    man = {"schema": "b04-stage-d-manifest-v1", "source_revision": R.PIN,
           "source_hashes": hashes, "synthetic": synthetic,
           "prior_merged_file_sha256": prior_hashes,
           "ordered_picks": picks,
           "segments": [{"name": name, "cipher_hex": bytes(c).hex()}
                        for name, c, _ in segments],
           "beam_width": H.BEAM_W, "max_skip": H.MAX_SKIP,
           "score_bar": -5.5,
           "native_key_rule": "len(ciphertext)+offset+512",
           "source_padding_rule": "beam_decode appends zero values if worst-case key length exceeds native key"}
    man["manifest_sha256"] = R.digest(man)
    return man


def decode_cell(row, segment, H, ks, sk):
    name, c0, c1 = segment
    offset = int(row.get("offset", 0) or 0)
    native_length = len(c0) + offset + 512
    key = ks.make_ks(row["gen"], row["red"],
                     bytes.fromhex(row["seed_hex"]), native_length)
    if row["dir"] == "rev":
        key = key[::-1]
    observed = ObservedKey(key, len(key))
    cipher = c0 if row["atbash"] == 0 else c1
    decoded = sk.beam_decode(cipher, observed, sign=row["sign"], o=offset,
                             beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    # Source stage_d copies exactly these row fields to the public result.
    value = {**{k: row[k] for k in ("seed", "seed_hex", "gen", "red", "sign",
                                    "atbash", "dir", "offset")},
             "head_score": row["score"], "score": decoded["score"],
             "text": decoded["translit"][:96]}
    audit = {**observed.reads, "native_key_length": len(key),
             "padding_branch_taken": observed.reads["extension_count"] > 0,
             "source_zero_padding_read": observed.reads["padded_read_count"] > 0,
             "final_pointer": decoded["ptr_end"],
             "decoded_runes": len(decoded["plain_idx"])}
    return value, audit


def verify_cell(path, manifest_hash, segment_index, pick_index):
    envelope = json.loads(path.read_text(encoding="utf-8"))
    body = envelope["payload"]
    if (R.digest(body) != envelope["payload_sha256"] or
        body["manifest_sha256"] != manifest_hash or
        body["segment_index"] != segment_index or
        body["pick_index"] != pick_index):
        raise ValueError(f"invalid Stage D checkpoint: {path}")
    return body


def summarize(cells, segments, picks, bar):
    summaries = []
    for si, seg in enumerate(segments):
        rows = [cells[(si, pi)]["source_row"] for pi in range(len(picks))]
        rows.sort(key=lambda row: -row["score"])
        summaries.append({"stage": f"D_{seg[0]}", "n_decodes": len(rows),
                          "elapsed_s": None,
                          "best_score": rows[0]["score"] if rows else None,
                          "bar": bar,
                          "hit": bool(rows and rows[0]["score"] >= bar),
                          "over_bar": [row for row in rows if row["score"] >= bar],
                          "n_improved_on_longer_text": sum(
                              row["score"] > row["head_score"] for row in rows),
                          "top50": rows[:50]})
    return summaries


def execute(source_root, output, synthetic=False, prior_paths=None,
            prior_check_paths=None,
            allow_full=False, max_cells=None, nproc=1):
    if nproc < 1:
        raise ValueError("nproc must be positive")
    if not synthetic and not allow_full:
        raise ValueError("real Stage D is held; --allow-full requires completed A/B/C")
    H, S, ks, sk, hashes = R.load_source(source_root)
    if synthetic:
        priors, segments = synthetic_inputs(H, sk)
        prior_hashes = {}
    else:
        if (not prior_paths or len(prior_paths) != 3 or
            not prior_check_paths or len(prior_check_paths) != 3):
            raise ValueError("real Stage D requires A/B/C merged files and independent checks")
        priors, prior_hashes = load_priors(prior_paths, prior_check_paths)
        segments = [H.full_page0(), H.full_unsolved()]
    man = make_manifest(H, hashes, priors, prior_hashes, segments, synthetic)
    output.mkdir(parents=True, exist_ok=True)
    mp = output / "manifest.json"
    if mp.exists():
        if json.loads(mp.read_text(encoding="utf-8")) != man:
            raise ValueError("Stage D checkpoint manifest changed")
    else:
        if any(output.iterdir()):
            raise ValueError("nonempty Stage D output without manifest")
        R.atomic_json(mp, man)
    picks = man["ordered_picks"]
    pending = []
    cells = {}
    for si in range(len(segments)):
        for pi in range(len(picks)):
            path = output / f"cell-{si:02d}-{pi:03d}.json"
            if path.exists():
                cells[(si, pi)] = verify_cell(path, man["manifest_sha256"], si, pi)
            else:
                pending.append((si, pi, path))
    selected = pending if max_cells is None else pending[:max_cells]
    t0 = time.monotonic()
    def save_cell(si, pi, value, audit):
        path = output / f"cell-{si:02d}-{pi:03d}.json"
        body = {"schema": "b04-stage-d-cell-v1",
                "manifest_sha256": man["manifest_sha256"],
                "segment_index": si, "pick_index": pi,
                "source_row": value, "key_access_audit": audit}
        R.atomic_json(path, {"payload": body, "payload_sha256": R.digest(body)})
        cells[(si, pi)] = body

    if nproc == 1:
        for si, pi, _ in selected:
            value, audit = decode_cell(picks[pi], segments[si], H, ks, sk)
            save_cell(si, pi, value, audit)
    elif selected:
        with Pool(nproc, initializer=_init_d_worker,
                  initargs=(str(source_root), segments, picks)) as pool:
            for si, pi, value, audit in pool.imap_unordered(
                    _work_d_indexed, [(si, pi) for si, pi, _ in selected]):
                save_cell(si, pi, value, audit)
    complete = len(cells) == len(picks) * len(segments)
    result = {"schema": "b04-stage-d-merge-v1",
              "manifest_sha256": man["manifest_sha256"],
              "complete": complete, "cells_saved": len(cells),
              "cells_expected": len(picks) * len(segments),
              "elapsed_this_invocation_s": time.monotonic() - t0}
    if complete:
        result["source_stage_summaries"] = summarize(cells, segments, picks,
                                                      man["score_bar"])
        result["cells_reading_padded_zero"] = sum(
            body["key_access_audit"]["source_zero_padding_read"]
            for body in cells.values())
        R.atomic_json(output / "merged.json", result)
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source-root", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--allow-full", action="store_true")
    ap.add_argument("--prior-a", type=pathlib.Path)
    ap.add_argument("--prior-b", type=pathlib.Path)
    ap.add_argument("--prior-c", type=pathlib.Path)
    ap.add_argument("--prior-a-check", type=pathlib.Path)
    ap.add_argument("--prior-b-check", type=pathlib.Path)
    ap.add_argument("--prior-c-check", type=pathlib.Path)
    ap.add_argument("--max-cells", type=int)
    ap.add_argument("--nproc", type=int, default=1)
    args = ap.parse_args()
    if args.max_cells is not None and args.max_cells < 0:
        ap.error("max-cells must be nonnegative")
    if args.nproc < 1:
        ap.error("nproc must be positive")
    prior_paths = ([args.prior_a, args.prior_b, args.prior_c]
                   if not args.synthetic else None)
    prior_check_paths = ([args.prior_a_check, args.prior_b_check,
                          args.prior_c_check] if not args.synthetic else None)
    if prior_paths and any(path is None for path in prior_paths):
        ap.error("real Stage D requires --prior-a, --prior-b and --prior-c")
    if prior_check_paths and any(path is None for path in prior_check_paths):
        ap.error("real Stage D requires --prior-a-check, --prior-b-check and --prior-c-check")
    print(json.dumps(execute(args.source_root.resolve(), args.output.resolve(),
                             args.synthetic, prior_paths, prior_check_paths,
                             args.allow_full,
                             args.max_cells, args.nproc), sort_keys=True))
