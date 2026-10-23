"""Independent row, group and source-gate check for Round 19 I1 G-FIX."""
from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ("repo_ms3", "exact_ms8", "exact_auto", "pair_ms8", "drift_l0",
         "drift_l4", "drift_l8", "drift_l16", "drift_mf1", "drift_mf3")


def cases(length):
    scaled = lambda n: max(1, round(n * length / 240))
    return (
        ("keyskip supp=0.83 (BASELINE)", "keyskip", False),
        ("skip_by_two supp=0.5", "skip_by_two", True),
        ("skip_by_two supp=0.83", "skip_by_two", True),
        ("skip_by_two supp=1.0", "skip_by_two", True),
        ("free_drift q=0.05", "free_drift", True),
        ("free_drift q=0.10", "free_drift", True),
        (f"drift_at n=5/240 (={scaled(5)})", "drift_at", True),
        (f"drift_at n=10/240 (={scaled(10)})", "drift_at", True),
        ("two-draws: coin_from_key supp=0.83", "coin_from_key", True),
        ("runs r=16 supp=1.0", "keyskip", True),
        ("runs r=32 supp=1.0", "keyskip", True),
        ("free_drift q=0.02", "free_drift", False),
        ("drift_at n=1/240", "drift_at", False),
        ("runs r=8 supp=1.0", "keyskip", False),
        ("keyskip supp=1.0", "keyskip", False),
    )


def median(values):
    ordered = sorted(values)
    n = len(ordered)
    return ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2


def row_index(rows, expected):
    found = {}
    for row in rows:
        key = (row["L"], row["label"], row["mode"], row["seed"])
        assert key not in found, f"duplicate row: {key}"
        assert key in expected, f"unexpected row: {key}"
        assert row["mech"] == expected[key][0], key
        assert set(row) == {"label", "mech", "L", "seed", "mode", "score",
                            "recovery", "n_skips_inferred", "n_unexplained",
                            "true_skips", "max_skip_used", "ct_doublet_pct", "secs"}
        assert 0 <= row["recovery"] <= 1
        assert 0 <= row["ct_doublet_pct"] <= 100
        assert row["secs"] > 0
        found[key] = row
    assert set(found) == set(expected), f"missing {len(set(expected)-set(found))} rows"
    return found


def group_index(groups, expected):
    found = {}
    for row in groups:
        key = (row["L"], row["label"], row["mode"])
        assert key not in found and key in expected, f"duplicate/unexpected group: {key}"
        assert row["in_gate"] is expected[key]
        found[key] = row
    assert set(found) == set(expected)
    return found


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest() == "2dc04804402079aa56ace46e1dcfcdd53c882149cb3d00fed4bb569df4965c00"
    for rel, digest in plan["source_files_sha256"].items():
        assert hashlib.sha256((HERE / "source" / rel).read_bytes()).hexdigest() == digest, rel
    source_path = HERE / "source/liber-primus/analysis/round19/I1/out_fix.json"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == plan["archived_output_sha256"]
    archive = json.loads(source_path.read_text(encoding="utf-8"))
    replay = json.loads((HERE / "replayed-out_fix.json").read_text(encoding="utf-8"))
    assert {k: v for k, v in archive.items() if k not in ("rows", "summary")} == \
           {k: v for k, v in replay.items() if k not in ("rows", "summary")}
    assert archive["stage"] == "fix" and archive["lane"] == "round19/I1"
    assert archive["beam_w"] == 400 and archive["n_seeds"] == 7
    assert archive["lengths"] == [240, 400] and tuple(archive["modes"]) == MODES
    assert archive["bar_score"] == -5.5 and archive["bar_recovery"] == .9
    addendum_path = HERE / "precision-addendum.json"
    addendum = json.loads(addendum_path.read_text(encoding="utf-8"))
    tolerance = addendum["diagnostic_absolute_tolerance"]
    assert tolerance == 3e-15

    expected_rows = {}
    expected_groups = {}
    for length in (240, 400):
        assert len(cases(length)) == 15
        for label, mechanism, gate in cases(length):
            for mode in MODES:
                expected_groups[(length, label, mode)] = gate
                for seed in range(7):
                    expected_rows[(length, label, mode, seed)] = (mechanism, gate)
    old = row_index(archive["rows"], expected_rows)
    new = row_index(replay["rows"], expected_rows)
    assert len(old) == len(new) == 2100
    score_deltas = []
    for key in expected_rows:
        assert {k: v for k, v in old[key].items() if k not in ("secs", "score")} == \
               {k: v for k, v in new[key].items() if k not in ("secs", "score")}, key
        delta = abs(old[key]["score"] - new[key]["score"])
        assert delta <= tolerance, (key, delta)
        if delta:
            score_deltas.append(delta)
    old_groups = group_index(archive["summary"], expected_groups)
    new_groups = group_index(replay["summary"], expected_groups)
    assert len(old_groups) == len(new_groups) == 300
    summary_score_deltas = []
    gate_by_mode = Counter()
    gate_total_by_mode = Counter()
    gate_by_mechanism = Counter()
    gate_total_by_mechanism = Counter()
    for (length, label, mode), is_gate in expected_groups.items():
        a, b = old_groups[(length, label, mode)], new_groups[(length, label, mode)]
        score_fields = ("median_score", "min_score", "max_score")
        assert {k: v for k, v in a.items() if k not in (*score_fields, "median_secs")} == \
               {k: v for k, v in b.items() if k not in (*score_fields, "median_secs")}, (length, label, mode)
        for field in score_fields:
            delta = abs(a[field] - b[field])
            assert delta <= tolerance, (length, label, mode, field, delta)
            if delta:
                summary_score_deltas.append(delta)
        selected = [new[(length, label, mode, seed)] for seed in range(7)]
        assert len({r["max_skip_used"] for r in selected}) == 1, (length, label, mode)
        sc = [r["score"] for r in selected]
        rc = [r["recovery"] for r in selected]
        measured = {
            "n_seeds": 7, "median_score": median(sc), "min_score": min(sc),
            "max_score": max(sc), "median_recovery": median(rc),
            "min_recovery": min(rc),
            "frac_over_bar": sum(s >= -5.5 and r >= .9 for s, r in zip(sc, rc)) / 7,
            "median_ct_doublet_pct": median(r["ct_doublet_pct"] for r in selected),
            "median_secs": median(r["secs"] for r in selected),
            "max_skip_used": selected[0]["max_skip_used"],
            "PASS": median(sc) >= -5.5 and median(rc) >= .9,
        }
        assert {k: b[k] for k in measured} == measured, (length, label, mode)
        assert b["median_secs"] > 0 and a["median_secs"] > 0
        if is_gate:
            mechanism = expected_rows[(length, label, mode, 0)][0]
            gate_total_by_mode[mode] += 1
            gate_total_by_mechanism[mechanism] += 1
            gate_by_mode[mode] += measured["PASS"]
            gate_by_mechanism[mechanism] += measured["PASS"]

    assert len(score_deltas) == addendum["observed_row_score_mismatches"] == 88
    assert len(summary_score_deltas) == addendum["observed_summary_score_mismatches"] == 8
    assert max(score_deltas) == addendum["max_observed_row_score_delta"]
    assert max(summary_score_deltas) == addendum["max_observed_summary_score_delta"]
    example_label = "skip_by_two supp=0.83"
    example = [{"mode": mode, "recovery": new[(240, example_label, mode, 0)]["recovery"],
                "score": new[(240, example_label, mode, 0)]["score"]}
               for mode in ("repo_ms3", "drift_l8")]
    output = {
        "schema": "liberpedia-round19-i1-fix-controls-v1",
        "plan_sha256": hashlib.sha256((HERE / "plan.json").read_bytes()).hexdigest(),
        "source_id": ["I1-02", "I1-05"],
        "frozen_exact_non_timing_acceptance_met": False,
        "post_result_numeric_diagnostic_passed": True,
        "precision_addendum_sha256": hashlib.sha256(addendum_path.read_bytes()).hexdigest(),
        "source_rows_compared": 2100,
        "source_groups_compared": 300,
        "row_scores_with_tiny_roundoff": len(score_deltas),
        "largest_row_score_delta": max(score_deltas, default=0),
        "summary_score_fields_with_tiny_roundoff": len(summary_score_deltas),
        "largest_summary_score_delta": max(summary_score_deltas, default=0),
        "non_score_non_timing_fields_exact": True,
        "score_absolute_tolerance": tolerance,
        "gated_groups": sum(gate_total_by_mode.values()),
        "gated_groups_passing": sum(gate_by_mode.values()),
        "illustrative_same_message_and_key": {"construction": example_label,
                                             "length": 240, "seed": 0,
                                             "selected_after_source_results": True,
                                             "decoders": example},
        "by_mode": [{"mode": mode, "passed": gate_by_mode[mode],
                     "gated": gate_total_by_mode[mode]} for mode in MODES],
        "by_construction": [{"mechanism": name, "passed": gate_by_mechanism[name],
                             "gated": gate_total_by_mechanism[name]}
                            for name in sorted(gate_total_by_mechanism)],
        "scope": "Known-key synthetic decoder power at 240 and 400 runes; no LP2 candidate key or cipher test.",
    }
    path = HERE / "results.json"
    if path.exists():
        assert json.loads(path.read_text(encoding="utf-8")) == output
    else:
        path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("PASS 2,100 source rows, 300 independent summaries and skip-bound checks; tiny score roundoff bounded")


if __name__ == "__main__":
    main()
