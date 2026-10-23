"""Independently audit the full pinned B04 Stage D checkpoint set.

No decoding is performed here. The direct original-decoder validation of
preselected book cells is a separate check after the accelerated run.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PERF = HERE.parent
D_PATH = PERF / "b04-stage-b-2026-10-23/resumable_d.py"
spec = importlib.util.spec_from_file_location("b04_d", D_PATH)
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)
R = D.R


def canonical_counter(rows):
    return collections.Counter(json.dumps(row, ensure_ascii=False,
                                          sort_keys=True, separators=(",", ":"))
                               for row in rows)


def check(source_root, output):
    H, _, _, _, source_hashes = R.load_source(source_root)
    plan_path = HERE / "plan-frozen.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    manifest_path = output / "manifest.json"
    man = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert man["manifest_sha256"] == R.digest({k: v for k, v in man.items()
                                                if k != "manifest_sha256"})
    assert man["schema"] == "b04-stage-d-manifest-v2"
    assert man["source_revision"] == R.PIN == plan["source_revision"]
    assert man["source_hashes"] == source_hashes
    assert man["synthetic"] is False
    assert man["decoder_backend"]["name"] == "prefix_shared"
    assert man["decoder_backend"]["wrapper_sha256"] == R.sha(D_PATH) == plan["runner_sha256"]
    assert man["decoder_backend"]["implementation_sha256"] == R.sha(D.FAST_BACKEND) == plan["decoder_implementation_sha256"]
    assert man["beam_width"] == H.BEAM_W and man["max_skip"] == H.MAX_SKIP
    assert man["score_bar"] == -5.5
    segments = [H.full_page0(), H.full_unsolved()]
    assert man["segments"] == [{"name": name, "cipher_hex": bytes(c).hex()}
                               for name, c, _ in segments]
    assert [len(s[1]) for s in segments] == [262, 12956]
    prior_paths = [pathlib.Path(plan["prior_inputs"][stage]["merged_path"])
                   for stage in "ABC"]
    check_paths = [pathlib.Path(plan["prior_inputs"][stage]["independent_check_path"])
                   for stage in "ABC"]
    priors, prior_hashes = D.load_priors(prior_paths, check_paths)
    assert man["prior_merged_file_sha256"] == prior_hashes
    picks = D.select_picks(priors)
    assert man["ordered_picks"] == picks
    assert len(picks) == 150 and R.digest(picks) == plan["ordered_candidate_sha256"]
    frozen = json.loads(pathlib.Path(plan["frozen_candidates_path"]).read_text(encoding="utf-8"))
    assert picks == frozen["ordered_candidates"]

    cells = {}
    zero_padding_reads = 0
    for si, seg in enumerate(segments):
        for pi, pick in enumerate(picks):
            path = output / f"cell-{si:02d}-{pi:03d}.json"
            envelope = json.loads(path.read_text(encoding="utf-8"))
            cell = envelope["payload"]
            assert envelope["payload_sha256"] == R.digest(cell)
            assert cell["schema"] == "b04-stage-d-cell-v1"
            assert (cell["manifest_sha256"], cell["segment_index"], cell["pick_index"]) == (
                man["manifest_sha256"], si, pi)
            row, audit = cell["source_row"], cell["key_access_audit"]
            assert row["head_score"] == pick["score"]
            assert {k: row[k] for k in ("seed", "seed_hex", "gen", "red", "sign",
                                         "atbash", "dir", "offset")} == {
                k: pick[k] for k in ("seed", "seed_hex", "gen", "red", "sign",
                                       "atbash", "dir", "offset")}
            assert len(row["text"]) <= 96
            assert audit["decoded_runes"] == len(seg[1])
            assert audit["native_key_length"] > 0
            assert audit["padded_read_count"] >= 0
            assert audit["source_zero_padding_read"] == (audit["padded_read_count"] > 0)
            zero_padding_reads += audit["source_zero_padding_read"]
            cells[(si, pi)] = cell
    assert len(cells) == 300
    merged_path = output / "merged.json"
    merged = json.loads(merged_path.read_text(encoding="utf-8"))
    assert merged["manifest_sha256"] == man["manifest_sha256"]
    assert merged["complete"] is True
    assert (merged["cells_saved"], merged["cells_expected"]) == (300, 300)
    assert merged["decoder_backend"] == "prefix_shared"
    assert merged["cells_reading_padded_zero"] == zero_padding_reads

    recomputed = []
    for si, segment in enumerate(segments):
        rows = sorted((cells[(si, pi)]["source_row"] for pi in range(150)),
                      key=lambda row: -row["score"])
        recomputed.append({"stage": f"D_{segment[0]}", "n_decodes": 150,
                           "elapsed_s": None, "best_score": rows[0]["score"],
                           "bar": -5.5,
                           "hit": rows[0]["score"] >= -5.5,
                           "over_bar": [r for r in rows if r["score"] >= -5.5],
                           "n_improved_on_longer_text": sum(r["score"] > r["head_score"]
                                                            for r in rows),
                           "top50": rows[:50]})
    assert merged["source_stage_summaries"] == recomputed

    source_results_path = source_root / "liber-primus/analysis/round13/B04/results_D.json"
    archived = json.loads(source_results_path.read_text(encoding="utf-8"))
    archived_comparison = {}
    for got, old in zip(recomputed, archived):
        fields = ("stage", "n_decodes", "best_score", "bar", "hit",
                  "over_bar", "n_improved_on_longer_text")
        key_of = lambda row: (row["seed_hex"], row["gen"], row["red"],
                              row["sign"], row["atbash"], row["dir"],
                              row["offset"])
        fresh_keys = collections.Counter(map(key_of, got["top50"]))
        old_keys = collections.Counter(map(key_of, old["top50"]))
        cutoff = got["top50"][-1]["score"]
        all_rows = [cells[(0 if got["stage"] == "D_page0_full" else 1, pi)]
                    ["source_row"] for pi in range(150)]
        by_key = {key_of(row): row for row in all_rows}
        assert len(by_key) == 150
        archived_missing = [list(key_of(row)) for row in old["top50"]
                            if key_of(row) not in by_key]
        archived_different = [list(key_of(row)) for row in old["top50"]
                              if key_of(row) in by_key and
                              row != by_key[key_of(row)]]
        archived_comparison[got["stage"]] = {
            "field_matches": {key: got[key] == old[key] for key in fields},
            "top50_score_order_equal": [r["score"] for r in got["top50"]] ==
                                          [r["score"] for r in old["top50"]],
            "top50_row_multiset_equal": canonical_counter(got["top50"]) ==
                                         canonical_counter(old["top50"]),
            "top50_exact_order_equal": got["top50"] == old["top50"],
            "top50_cutoff_score": cutoff,
            "cutoff_score_ties_among_all_150": sum(row["score"] == cutoff
                                                    for row in all_rows),
            "top50_fresh_only_keys": [list(k) for k in
                                      (fresh_keys - old_keys).elements()],
            "top50_archived_only_keys": [list(k) for k in
                                         (old_keys - fresh_keys).elements()],
            "archived_top50_tuple_keyed_missing_keys": archived_missing,
            "archived_top50_tuple_keyed_different_rows": archived_different,
            "archived_top50_tuple_keyed_exact_rows": (
                50 - len(archived_missing) - len(archived_different)),
        }
    return {"schema": "b04-stage-d-independent-check-v1",
            "source_revision": R.PIN,
            "frozen_plan_sha256": R.sha(plan_path),
            "manifest_file_sha256": R.sha(manifest_path),
            "manifest_sha256": man["manifest_sha256"],
            "merged_file_sha256": R.sha(merged_path),
            "archived_source_result_sha256": R.sha(source_results_path),
            "candidate_sha256": R.digest(picks),
            "cells_checked": len(cells),
            "cells_reading_padded_zero": zero_padding_reads,
            "independent_merge_exact": True,
            "archived_source_comparison": archived_comparison,
            "result_summaries": [{k: s[k] for k in ("stage", "best_score", "hit",
                                                  "n_improved_on_longer_text")}
                                 for s in recomputed],
            "scope_limit": "Checkpoint and summary verification; unchanged-source raw comparisons of 150 page cells and four preselected book cells are recorded separately in direct-original-validation.json."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = check(args.source_root.resolve(), args.output.resolve())
    path = HERE / "independent-check.json"
    path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
