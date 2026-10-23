"""Freeze the completed fresh A/B/C top-50 inputs to source Stage D.

This never decodes Stage D. It records equal-score ordering differences from
the pinned archive and the exact ordered tuple list our replay would use.
"""
import collections
import hashlib
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
WORK = pathlib.Path("C:/Users/ianex/Documents/Codex/2026-10-19/i-w/work")
SOURCE = WORK / "source-cache/dukotah-cicada3301/liber-primus/analysis/round13/B04"
D_SCRIPT = HERE.parent / "b04-stage-b-2026-10-23/resumable_d.py"
spec = importlib.util.spec_from_file_location("b04_resumable_d", D_SCRIPT)
D = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D)


def row_counter(rows):
    return collections.Counter(json.dumps(row, ensure_ascii=True,
                                          sort_keys=True) for row in rows)


def inspect():
    fresh = []
    source_summaries = []
    stage_checks = {}
    for stage in "ABC":
        merged_path = WORK / f"b04-lp2-{stage}-20261023/merged.json"
        merged = json.loads(merged_path.read_text(encoding="utf-8"))
        assert merged["complete"] and merged["n_decodes"] == merged["expected_decodes"]
        summary = merged["source_stage_summary"]
        archived = json.loads((SOURCE / f"results_{stage}.json").read_text(encoding="utf-8"))
        a, b = summary["top50"], archived["top50"]
        assert len(a) == len(b) == 50
        same_scores = [r["score"] for r in a] == [r["score"] for r in b]
        fresh_rows, source_rows = row_counter(a), row_counter(b)
        same_rows = fresh_rows == source_rows
        fresh.append(summary)
        source_summaries.append(archived)
        stage_checks[stage] = {
            "fresh_merged_sha256": hashlib.sha256(merged_path.read_bytes()).hexdigest(),
            "archived_result_sha256": hashlib.sha256((SOURCE / f"results_{stage}.json").read_bytes()).hexdigest(),
            "top50_row_multiset_equal": same_rows,
            "top50_score_order_equal": same_scores,
            "top50_exact_order_equal": a == b,
            "top50_fresh_only_rows": list((fresh_rows - source_rows).elements()),
            "top50_archived_only_rows": list((source_rows - fresh_rows).elements()),
            "cutoff_score": a[-1]["score"],
            "cutoff_score_ties_in_top50": sum(r["score"] == a[-1]["score"] for r in a),
        }
    picks = D.select_picks(fresh)
    source_picks = D.select_picks(source_summaries)
    assert 0 < len(picks) <= 150
    key_of = lambda row: (row.get("seed_hex"), row.get("gen"), row.get("red"),
                          row.get("sign"), row.get("atbash"), row.get("dir"),
                          row.get("offset"))
    fresh_keys = list(map(key_of, picks))
    source_keys = list(map(key_of, source_picks))
    fresh_only_keys = collections.Counter(fresh_keys) - collections.Counter(source_keys)
    archived_only_keys = collections.Counter(source_keys) - collections.Counter(fresh_keys)
    return {
        "schema": "b04-stage-d-frozen-input-candidates-v1",
        "stage_checks": stage_checks,
        "source_stage_d_sort": "stable concatenation A then B then C; score descending; first tuple retained",
        "candidate_count": len(picks),
        "ordered_candidate_sha256": D.R.digest(picks),
        "archived_candidate_count": len(source_picks),
        "fresh_vs_archived_candidate_key_multiset_equal": (
            collections.Counter(fresh_keys) == collections.Counter(source_keys)),
        "fresh_vs_archived_candidate_key_order_equal": fresh_keys == source_keys,
        "fresh_only_candidate_keys": [list(key) for key in fresh_only_keys.elements()],
        "archived_only_candidate_keys": [list(key) for key in archived_only_keys.elements()],
        "ordered_candidates": picks,
        "scope_limit": "Input list only; source Stage D full-page/book decoding has not run.",
    }


if __name__ == "__main__":
    data = inspect()
    path = HERE / "stage-d-frozen-candidates.json"
    path.write_text(json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")
    print(json.dumps({"candidate_count": data["candidate_count"],
                      "ordered_candidate_sha256": data["ordered_candidate_sha256"],
                      "fresh_vs_archived_candidate_key_multiset_equal": data["fresh_vs_archived_candidate_key_multiset_equal"],
                      "fresh_vs_archived_candidate_key_order_equal": data["fresh_vs_archived_candidate_key_order_equal"],
                      "top50_exact_order_equal": {s: x["top50_exact_order_equal"]
                                                  for s, x in data["stage_checks"].items()}},
                     sort_keys=True))
