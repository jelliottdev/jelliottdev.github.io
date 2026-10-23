"""Independent recount of the 336 source decoder-control rows."""
from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODES = ("repo_ms3", "exact_ms8", "pair_ms8", "drift_l0", "drift_l8", "drift_l16")
SUPP = (0.0, 0.4, 0.83, 1.0)


def equivalent(a, b):
    if isinstance(a, float) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=0, abs_tol=1e-9)
    return a == b


def check(replay_path: Path | None = None) -> dict:
    source = json.loads((HERE / "source/liber-primus/analysis/round19/I1/out_base.json").read_text(encoding="utf-8"))
    replay = json.loads((replay_path or HERE / "out_base.json").read_text(encoding="utf-8"))
    assert source["stage"] == replay["stage"] == "base"
    assert len(source["rows"]) == len(replay["rows"]) == 336
    assert len(source["summary"]) == len(replay["summary"]) == 48
    def index(rows):
        return {(r["L"], r["label"], r["mode"], r["seed"]): r for r in rows}
    srows, rrows = index(source["rows"]), index(replay["rows"])
    assert srows.keys() == rrows.keys()
    grouped = defaultdict(list)
    for key, b in rrows.items():
        a = srows[key]
        assert set(a) == set(b)
        assert all(equivalent(a[k], b[k]) for k in a if k != "secs"), key
        assert b["seed"] in range(7) and b["L"] in (240, 400)
        assert b["label"] in [f"keyskip supp={x}" for x in SUPP]
        assert b["mode"] in MODES
        grouped[key[:3]].append(b)
    assert len(grouped) == 48 and all(len(v) == 7 for v in grouped.values())
    summaries = {(r["L"], r["label"], r["mode"]): r for r in replay["summary"]}
    src_summaries = {(r["L"], r["label"], r["mode"]): r for r in source["summary"]}
    assert summaries.keys() == src_summaries.keys() == grouped.keys()
    for key, rows in grouped.items():
        s = summaries[key]
        old = src_summaries[key]
        assert set(s) == set(old)
        assert all(equivalent(s[k], old[k]) for k in s if k != "median_secs"), key
        for field, val in {
            "n_seeds": 7,
            "median_score": statistics.median(r["score"] for r in rows),
            "min_score": min(r["score"] for r in rows),
            "max_score": max(r["score"] for r in rows),
            "median_recovery": statistics.median(r["recovery"] for r in rows),
            "min_recovery": min(r["recovery"] for r in rows),
            "frac_over_bar": sum(r["score"] >= -5.5 and r["recovery"] >= 0.90 for r in rows) / 7,
            "median_ct_doublet_pct": statistics.median(r["ct_doublet_pct"] for r in rows),
            "max_skip_used": rows[0]["max_skip_used"],
        }.items():
            assert equivalent(s[field], val), (key, field, s[field], val)
        assert s["PASS"] == (s["median_score"] >= -5.5 and s["median_recovery"] >= .90)
    def get(supp, mode, L=240):
        return summaries[(L, f"keyskip supp={supp}", mode)]
    assert get(.83, "repo_ms3")["median_recovery"] == 1.0
    assert get(.83, "pair_ms8")["median_recovery"] < .40
    out = {
        "rows": len(rrows), "cells": len(grouped), "source_non_timing_rows_match": True,
        "pair_on_keyskip_supp083_L240": {
            "exact_decoder_recovery": get(.83, "repo_ms3")["median_recovery"],
            "pair_decoder_recovery": get(.83, "pair_ms8")["median_recovery"],
            "exact_decoder_score": get(.83, "repo_ms3")["median_score"],
            "pair_decoder_score": get(.83, "pair_ms8")["median_score"],
        },
    }
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    assert saved == out, "Saved summary differs from the independently recounted rows"
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    check()
