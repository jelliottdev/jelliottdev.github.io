"""Summarize the exact pinned Stage AE all-lag table and source controls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))


def build() -> dict:
    lags = rows("source-stage_ae_lags.tsv")
    controls = rows("source-stage_ae_controls.tsv")
    assert len(lags) == 12935 and [int(r["lag"]) for r in lags] == list(range(11, 12946))
    assert len(controls) == 10
    assert {(int(r["period"]), r["source"]) for r in controls} == {
        (period, source) for period in (1033, 1729, 3301, 6000, 9000)
        for source in ("E", "L")}
    assert {int(r["draws"]) for r in controls} == {10}
    count = Counter(r["verdict"] for r in lags)
    assert count["EXCLUDED"] == 10030 and count["-"] == 2905
    assert all(int(r["excluded"]) == 0 for r in controls)
    named = []
    for period in (1033, 1729, 3301):
        row = lags[period - 11]
        support = [r for r in controls if int(r["period"]) == period]
        named.append({
            "period": period, "pairs": int(row["pairs"]), "agreements": int(row["agreements"]),
            "observed_rate": float(row["rate"]), "lower_p_model": row["lower_p_model"],
            "verdict": row["verdict"],
            "minimum_planted_rate": min(float(r["rate_min"]) for r in support),
            "planted_passes": sum(int(r["passed"]) for r in support),
        })
    return {
        "schema": "liberpedia-wulfic-periodic-alphabet-results-v1",
        "plan_sha256": sha(HERE / "plan.json"),
        "source_commit": "bf89d3d13aad2b8f2c95ab195cf1b092f250775c",
        "source_tables": {name: sha(HERE / name) for name in
                          ("source-stage_ae_lags.tsv", "source-stage_ae_controls.tsv")},
        "lag_count": len(lags), "excluded": count["EXCLUDED"], "open": count["-"],
        "first_open_lag": min(int(r["lag"]) for r in lags if r["verdict"] == "-"),
        "named_periods": named,
        "control_draws": sum(int(r["draws"]) for r in controls),
        "control_exclusions": sum(int(r["excluded"]) for r in controls),
        "control_passes": sum(int(r["passed"]) for r in controls),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    path = HERE / "results.json"
    if args.check:
        assert path.read_text(encoding="utf-8") == content
        print("Wulfic Stage AE pinned all-lag tables: OK")
    else:
        path.write_text(content, encoding="utf-8", newline="\n")
