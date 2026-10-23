"""Compare preselected Stage D cells with the unchanged pinned source decoder.

Run only after the accelerated 300-cell campaign finishes. The four book
indices were frozen before target results; all page-0 cells are supplementary.
"""
import argparse
import importlib.util
import json
import pathlib
from multiprocessing import Pool

HERE = pathlib.Path(__file__).resolve().parent
PERF = HERE.parent
D_PATH = PERF / "b04-stage-b-2026-10-23/resumable_d.py"
spec = importlib.util.spec_from_file_location("b04_d", D_PATH)
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)

_STATE = {}


def init_worker(source_root, picks):
    H, _, ks, sk, _ = D.R.load_source(pathlib.Path(source_root))
    _STATE.update(H=H, ks=ks, sk=sk, picks=picks,
                  segments=[H.full_page0(), H.full_unsolved()],
                  fast_decoder=D.backend_decoder("prefix_shared"))


def one(task):
    si, pi = task
    row = _STATE["picks"][pi]
    segment = _STATE["segments"][si]
    H, ks, sk = (_STATE[k] for k in ("H", "ks", "sk"))
    if si == 0:
        value, audit = D.decode_cell(row, segment, H, ks, sk, backend="source")
        return si, pi, value, audit, None

    # A full raw-dictionary comparison is required for the four frozen book
    # cells. Wrapper rows retain only 96 transliteration characters.
    offset = int(row.get("offset", 0) or 0)
    native_length = len(segment[1]) + offset + 512
    key = ks.make_ks(row["gen"], row["red"],
                     bytes.fromhex(row["seed_hex"]), native_length)
    if row["dir"] == "rev":
        key = key[::-1]
    c = segment[1] if row["atbash"] == 0 else segment[2]
    source_key = D.ObservedKey(key, len(key))
    fast_key = D.ObservedKey(key, len(key))
    source_raw = sk.beam_decode(c, source_key, sign=row["sign"], o=offset,
                                beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    fast_raw = _STATE["fast_decoder"](c, fast_key, gp=sk.gp, Q=sk.Q,
                                       sign=row["sign"], o=offset,
                                       beam_w=H.BEAM_W, max_skip=H.MAX_SKIP)
    fields = ("score", "beam_score", "plain_idx", "translit", "ptr_end")
    assert set(source_raw) == set(fast_raw) == set(fields)
    full = {"raw_field_equal": {field: source_raw[field] == fast_raw[field]
                                for field in fields},
            "raw_field_source_sha256": {field: D.R.digest(source_raw[field])
                                        for field in fields},
            "raw_field_accelerated_sha256": {field: D.R.digest(fast_raw[field])
                                             for field in fields},
            "full_source_translit_length": len(source_raw["translit"]),
            "full_accelerated_translit_length": len(fast_raw["translit"]),
            "source_key_reads_sha256": D.R.digest(source_key.reads),
            "accelerated_key_reads_sha256": D.R.digest(fast_key.reads),
            "raw_key_reads_equal": source_key.reads == fast_key.reads}
    value = {**{k: row[k] for k in ("seed", "seed_hex", "gen", "red", "sign",
                                    "atbash", "dir", "offset")},
             "head_score": row["score"], "score": source_raw["score"],
             "text": source_raw["translit"][:96]}
    audit = {**source_key.reads, "native_key_length": len(key),
             "padding_branch_taken": source_key.reads["extension_count"] > 0,
             "source_zero_padding_read": source_key.reads["padded_read_count"] > 0,
             "final_pointer": source_raw["ptr_end"],
             "decoded_runes": len(source_raw["plain_idx"])}
    return si, pi, value, audit, full


def validate(source_root, output, workers):
    man = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    merged = json.loads((output / "merged.json").read_text(encoding="utf-8"))
    assert merged["complete"] and merged["cells_saved"] == 300
    picks = man["ordered_picks"]
    plan = json.loads((HERE / "plan-frozen.json").read_text(encoding="utf-8"))
    frozen_book = [(1, item["pick_index"])
                   for item in plan["holdout_validation_cells"]]
    assert frozen_book == [(1, 0), (1, 49), (1, 99), (1, 149)]
    tasks = [(0, i) for i in range(150)] + frozen_book
    comparisons = []
    with Pool(workers, initializer=init_worker,
              initargs=(str(source_root), picks)) as pool:
        for si, pi, value, audit, full in pool.imap_unordered(one, tasks):
            path = output / f"cell-{si:02d}-{pi:03d}.json"
            body = D.verify_cell(path, man["manifest_sha256"], si, pi)
            same_row = value == body["source_row"]
            same_audit = audit == body["key_access_audit"]
            comparisons.append({"segment_index": si, "pick_index": pi,
                                "source_row_sha256": D.R.digest(value),
                                "accelerated_row_sha256": D.R.digest(body["source_row"]),
                                "source_audit_sha256": D.R.digest(audit),
                                "accelerated_audit_sha256": D.R.digest(body["key_access_audit"]),
                                "all_returned_fields_equal": same_row,
                                "all_key_access_fields_equal": same_audit,
                                "full_raw_comparison": full})
    comparisons.sort(key=lambda row: (row["segment_index"], row["pick_index"]))
    result = {"schema": "b04-stage-d-original-decoder-validation-v1",
              "source_revision": D.R.PIN,
              "frozen_plan_sha256": D.R.sha(HERE / "plan-frozen.json"),
              "manifest_sha256": man["manifest_sha256"],
              "merged_file_sha256": D.R.sha(output / "merged.json"),
              "source_decoder_cells": len(comparisons),
              "page0_cells": sum(r["segment_index"] == 0 for r in comparisons),
              "preselected_book_indices": [r["pick_index"] for r in comparisons
                                           if r["segment_index"] == 1],
              "all_returned_fields_equal": all(r["all_returned_fields_equal"]
                                                for r in comparisons),
              "all_key_access_fields_equal": all(r["all_key_access_fields_equal"]
                                                  for r in comparisons),
              "all_frozen_book_raw_fields_equal": all(
                  all(r["full_raw_comparison"]["raw_field_equal"].values())
                  for r in comparisons if r["segment_index"] == 1),
              "all_frozen_book_raw_key_reads_equal": all(
                  r["full_raw_comparison"]["raw_key_reads_equal"]
                  for r in comparisons if r["segment_index"] == 1),
              "comparisons": comparisons}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    result = validate(args.source_root.resolve(), args.output.resolve(), args.workers)
    path = HERE / "direct-original-validation.json"
    path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    print(json.dumps({k: result[k] for k in
                      ("source_decoder_cells", "page0_cells", "preselected_book_indices",
                       "all_returned_fields_equal", "all_key_access_fields_equal",
                       "all_frozen_book_raw_fields_equal",
                       "all_frozen_book_raw_key_reads_equal")},
                     sort_keys=True))
