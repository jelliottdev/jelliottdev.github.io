"""Independent, standard-library audit of the 604 compact T2 probe rows."""
from __future__ import annotations

import hashlib
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    plan = json.loads((HERE / "plan.json").read_text(encoding="utf-8"))
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    doc = json.loads((HERE / "line-results.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "liberpedia-t2-compact-lines-v1"
    assert sha(HERE / "plan.json") == result["plan_sha256"]
    assert sha(HERE / "templates.npz") == plan["fresh_instrument"]["templates_npz_sha256"]
    assert sha(HERE / "diff_report.json") == plan["fresh_instrument"]["diff_report_sha256"]
    assert sha(HERE / "line-results.json") == result["line_results_sha256"]
    rows = doc["rows"]
    assert len(rows) == 604 and [r["gline"] for r in rows] == list(range(604))
    groups = {x: {"lines": 0, "slots": 0, "matches": 0, "positive_delta": 0}
              for x in ("pages-0-44", "source-segments-45-54", "solved-LP2")}
    changed = dict(best_sequence=0, costs=0, positions=0, failures=0)
    for r in rows:
        seg = r["seg"]
        assert r["num"] == (seg if seg <= 49 else seg + 1 if seg <= 54 else seg + 18), (seg, r["num"])
        group = "solved-LP2" if seg in (55, 56) else ("source-segments-45-54" if seg >= 45 else "pages-0-44")
        g = groups[group]
        n = len(r["canon"])
        assert n == len(r["fresh_best"]) == len(r["historical_best"]) == r["nrune"] - r["skip0"]
        for field in ("fresh_best_cost", "fresh_canon_cost", "historical_best_cost", "historical_canon_cost", "fresh_x", "historical_x"):
            assert len(r[field]) == n
        assert all(isinstance(x, int) and 0 <= x < 29 for x in r["canon"] + r["fresh_best"] + r["historical_best"])
        g["lines"] += 1
        g["slots"] += n
        g["matches"] += sum(a == b for a, b in zip(r["canon"], r["fresh_best"]))
        g["positive_delta"] += sum(a < b for a, b in zip(r["fresh_best_cost"], r["fresh_canon_cost"]))
        changed["best_sequence"] += r["fresh_best"] != r["historical_best"]
        changed["costs"] += (r["fresh_best_cost"], r["fresh_canon_cost"]) != (r["historical_best_cost"], r["historical_canon_cost"])
        changed["positions"] += r["fresh_x"] != r["historical_x"]
        changed["failures"] += r["fresh_fail"] != r["historical_fail"]
    assert groups == result["by_stratum"]
    assert changed == result["historical_row_differences"]
    assert groups["solved-LP2"] == {"lines": 10, "slots": 178, "matches": 178, "positive_delta": 0}
    assert sum(g["slots"] for g in groups.values()) == 13121
    assert sum(g["matches"] for g in groups.values()) == 13086
    assert changed == {"best_sequence": 0, "costs": 329, "positions": 262, "failures": 0}
    print("T2 fresh-template receipt checked: 604 lines, 13,121 positions; solved 178/178; unchanged choices, changed costs/positions")


if __name__ == "__main__":
    main()
