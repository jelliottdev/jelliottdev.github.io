"""Read-only, source-byte-pinned triage for seven Round 19 ledger entries.

This checks saved-row arithmetic and dependencies. It does not rerun beams or
language-model training, and its receipt says so explicitly.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO.parent / "source-cache" / "dukotah-cicada3301"
REV = "f08b20b632d91209ddbaa747e8e2f23df0c78ba1"
BASE = "liber-primus/analysis/round19/"


def blob(path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(SOURCE), "show", f"{REV}:{path}"])


def obj(path: str):
    return json.loads(blob(path))


def ev(paths: list[str]) -> list[dict]:
    return [{"path": p, "sha256": hashlib.sha256((REPO / p).read_bytes() if p.startswith("experiments/") else blob(p)).hexdigest()} for p in paths]


def near(a, b, tol=1e-10):
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def check_i1_rows():
    files = ["out_fp_deep.json", "out_fp_deep2.json", "out_fp_curve.json"]
    checked = 0
    errors = []
    particulars = []
    for name in files:
        d = obj(BASE + "I1/" + name)
        for s in d["summary"]:
            rows = [r for r in d["rows"] if r["null"] == s["null"] and r["mode"] == s["mode"]]
            scores = [r["score"] for r in rows]
            if len(rows) != s["n"] or not near(statistics.mean(scores), s["mean"]) or not near(max(scores), s["max"]):
                errors.append([name, s["null"], s["mode"], "n/mean/max"])
            if not near(sum(x > -5.5 for x in scores) / len(scores), s["frac_over_-5.5"]):
                errors.append([name, s["null"], s["mode"], "line crossing"])
            checked += 1
            if s["null"] == "real" and s["mode"] in ("drift_l0", "drift_l4", "drift_l8", "repo_ms3"):
                particulars.append({"file": name, "mode": s["mode"], "n": s["n"], "mean": s["mean"], "over_minus_5_5": sum(x > -5.5 for x in scores)})
    return {"saved_cells_recounted": checked, "errors": errors, "illustrative_real_nulls": particulars}


def check_r1():
    a = obj(BASE + "R1/out_a.json")
    a2 = obj(BASE + "R1/out_a2.json")
    b = obj(BASE + "R1/out_b.json")
    base = next(x for x in a["frontier"] if x["label"] == "exact/ms3")
    mismatches = []
    for x in a["frontier"]:
        for prefix in ("keyskip", "skip2", "drift"):
            actual = x[prefix]["median_score"] - x["null"]["bar_1e+06"]
            if not near(actual, x["sep_" + prefix + "_vs_bar1e6"]):
                mismatches.append([x["label"], prefix])
    evs = b["B_i"]["eigenvalues"]
    p = len(evs)
    nyholt = 1 + (p - 1) * (1 - statistics.pvariance(evs) / p)
    liji = sum((1 if x >= 1 else 0) + (x - math.floor(x)) for x in evs)
    if not near(nyholt, b["B_i"]["M_eff_nyholt"]) or not near(liji, b["B_i"]["M_eff_liji"]):
        mismatches.append(["B_i", "eigenvalue estimators"])
    fpr = b["B_ii"]
    return {"A_frontier_cells": len(a["frontier"]), "A2_frontier_cells": len(a2["frontier"]),
            "A_baseline_null_mean": base["null"]["mean"], "B_LiJi": liji,
            "B_max_panel_FPR": fpr["fpr_max_over_panel"], "B_English_only_FPR": fpr["fpr_english_only"],
            "saved_derived_arithmetic_errors": mismatches,
            "note": "Saved aggregate arithmetic only; no source beam, LM, or null draws rerun."}


def check_i3_i2():
    c = obj(BASE + "I3/calib19.json")
    s = obj(BASE + "I3/out_summary.json")
    i2 = obj(BASE + "I2/out_gates.json")
    cells = c["cells"]
    return {"I3_saved_calibration_objects": len(cells),
            "I3_summary_G_CAL": s["gates"].get("G-CAL"),
            "I3_summary_G_CAL_X": s["gates"].get("G-CAL-X"),
            "I2_saved_gate_verdicts": {k: v.get("passed") if isinstance(v, dict) else None for k, v in i2["gates"].items()},
            "note": "Saved values identified; model-dependent scores and 9.6 million source null decodes not rerun."}


def source_exists(path: str) -> bool:
    p = subprocess.run(["git", "-C", str(SOURCE), "cat-file", "-e", f"{REV}:{path}"], capture_output=True)
    return p.returncode == 0


def main():
    got = subprocess.check_output(["git", "-C", str(SOURCE), "rev-parse", "HEAD"], text=True).strip()
    assert got == REV, (got, REV)
    i1 = check_i1_rows()
    r1 = check_r1()
    i3i2 = check_i3_i2()
    assert not i1["errors"] and not r1["saved_derived_arithmetic_errors"]
    miss = [p for p in ["liber-primus/data/keys/king_in_yellow.txt",
                        "liber-primus/data/keys/welsh/welsh_mabinogion.txt",
                        "liber-primus/analysis/round19/I2/models/panel.npz"] if not source_exists(p)]
    out = {"schema": "liberpedia-batch20-worker-a-v1", "source_revision": REV,
           "source_root": str(SOURCE), "checks": {"I1_saved_rows": i1, "R1_saved_arithmetic": r1,
                                                  "I3_I2_saved_gates": i3i2},
           "absent_from_pinned_git": miss,
           "entries": [
               {"source_id": "I1-03", "state": "partial", "evidence": ev([BASE+"I1/ledger.json", BASE+"I1/out_fp_deep.json", BASE+"I1/out_fp_deep2.json", BASE+"I1/out_fp_curve.json", BASE+"I1/out_fp_tail.json", "experiments/records/round19-decoder-null-bars/record.json"]), "executions": [], "covered_subclaim": "Published round19-decoder-null-bars replayed all 26 source fits from 34,000 saved score rows; this audit recounts the saved means, maxima and line crossings for all I1 FP arrays.", "remaining": ["Original 34,000 wrong-key beam decodes not rerun; far-tail extrapolation not empirically validated."]},
               {"source_id": "I1-06", "state": "partial", "evidence": ev([BASE+"I1/ledger.json", BASE+"I1/out_base.json", BASE+"I1/out_fp_curve.json", "experiments/records/round19-decoder-baseline-control/record.json", "experiments/records/round19-decoder-null-bars/record.json"]), "executions": [], "covered_subclaim": "Published G-BASE replays 336 known-key decoder controls; null-bars independently recounts 500/500 wrong-key line crossings in permissive lambda=0 saved scores.", "remaining": ["Original FP beam decoding not freshly replayed; score over a line is not recovery."]},
               {"source_id": "I1-09", "state": "partial", "evidence": ev([BASE+"I1/ledger.json", BASE+"I1/RESULTS.md", BASE+"I1/driftbeam.py", BASE+"I1/run_gates.py", "experiments/records/round19-decoder-baseline-control/record.json", "experiments/records/round19-decoder-null-bars/record.json", "experiments/records/round19-decoder-repair-controls/record.json"]), "executions": [], "covered_subclaim": "Known-key source gates and decoder-specific wrong-key score behavior have partial published control coverage; this entry is a recommended handoff policy, not an LP2 key test.", "remaining": ["Adaptive max_skip policy plus its own wrong-key null and I3 mu/beta handoff not independently replayed together."]},
               {"source_id": "R19-R1-A", "state": "partial", "evidence": ev([BASE+"R1/ledger.json", BASE+"R1/RESULTS.md", BASE+"R1/a_permissive.py", BASE+"R1/a2_union.py", BASE+"R1/a3_effperm.py", BASE+"R1/r1_lib.py", BASE+"R1/out_a.json", BASE+"R1/out_a2.json", BASE+"R1/out_a3.json"]), "executions": [], "covered_subclaim": "Saved R1 frontier arithmetic checked, including 16 + 6 configurations; related decoder mechanics covered by published controls but this independent source frontier has not been rerun.", "remaining": ["Exact source corpus king_in_yellow.txt is absent from pinned Git and not recovered; source R1 A beam/null grids remain unrun."]},
               {"source_id": "R19-R1-B", "state": "blocked", "evidence": ev([BASE+"R1/ledger.json", BASE+"R1/RESULTS.md", BASE+"R1/b_panel.py", BASE+"R1/r1_lib.py", BASE+"R1/out_b.json"]), "executions": [], "covered_subclaim": "Saved eigenvalue effective-test estimator arithmetic checked; no exact model/control replay.", "remaining": ["R1 register builder needs missing king_in_yellow.txt and Welsh mabinogion bytes; full B-i through B-iv panel and beam tests blocked."]},
               {"source_id": "R19-I3-NULLS", "state": "partial", "evidence": ev([BASE+"I3/ledger.json", BASE+"I3/RESULTS.md", BASE+"I3/calib19.json", BASE+"I3/out_summary.json", BASE+"I3/nullcurve19.py", BASE+"I3/summary.py", BASE+"I3/test_i3.py"]), "executions": [], "covered_subclaim": "Source calibration objects, summaries and I3 test implementation pinned; null score generation not replayed.", "remaining": ["Nine-register I2 model unavailable; 9.6 million wrong-key decodes and far-tail calibration not independently replayed."]},
               {"source_id": "I2-MULTI-REGISTER-ADJUDICATOR", "state": "blocked", "evidence": ev([BASE+"I2/ledger.json", BASE+"I2/RESULTS.md", BASE+"I2/adjudicate.py", BASE+"I2/build_models.py", BASE+"I2/power.py", BASE+"I2/out_build.json", BASE+"I2/out_power.json", BASE+"I2/out_gates.json"]), "executions": [], "covered_subclaim": "Nine-model source inputs and saved gate reports pinned; English-only and other published scorer controls are different instruments.", "remaining": ["Gitignored models/panel.npz and models/testhalves.npz absent; exact Welsh corpus hash in out_build not recovered; source nine-register scores and gates cannot be replayed from saved results alone."]},
           ]}
    audit_execution = {"command": "python -X utf8 research/source-intake/batch20-2026-10-23/worker-a/audit.py", "exit_code": 0,
                       "workdir": str(REPO),
                       "output_path": "research/source-intake/batch20-2026-10-23/worker-a/receipt.json",
                       "scope": "Saved-row recount and saved-derived arithmetic; no beam or language model rerun."}
    i3_execution = {"command": "$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; python -m pytest liber-primus/analysis/round19/I3/test_i3.py -q",
                    "exit_code": 0, "workdir": str(SOURCE),
                    "output_path": "research/source-intake/batch20-2026-10-23/worker-a/i3-pytest.log",
                    "scope": "15 source unit tests; no null-decoding campaign."}
    for entry in out["entries"]:
        entry["executions"] = [audit_execution]
        if entry["source_id"] == "R19-I3-NULLS":
            entry["executions"].append(i3_execution)
    path = HERE / "receipt.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(path)
    print("entries", len(out["entries"]), "I1 cells", i1["saved_cells_recounted"], "R1 A", r1["A_frontier_cells"])


if __name__ == "__main__":
    main()
