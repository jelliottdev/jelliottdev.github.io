#!/usr/bin/env python3
"""Check the pinned selection/acrostic source receipts and final-gate arithmetic.

This is a receipt and decision-rule audit. It does not rerun the upstream null
draws; those were replayed separately in research/dukotah-r23-a2-source-audit.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    old = load("source-r22-results.json")
    new = load("source-r23-results.json")
    result = load("results.json")

    assert old["lane"] == "R22-A-SELFEMBEDDED-READ"
    assert new["lane"] == "R23-A2-LINE-ACROSTIC"
    assert old["seed"] == new["seed"] == 3301
    assert old["n_shuffles"] == new["n_shuffles"] == 1000
    assert [(s["stream"], s["n_selections"], s["n_survivors_percell"],
             s["n_survivors_family"]) for s in old["streams"]] == [
                 ("letters", 1754, 4, 0), ("runes", 1754, 2, 0)]
    assert (new["n_candidates"], new["n_distinct_lengths"],
            new["n_survivors_percell"], new["n_survivors_family"]) == (48, 20, 1, 0)
    assert len(new["all_candidates_sorted"]) == 48
    assert sum(r["survivor_percell"] for r in new["all_candidates_sorted"]) == 1
    assert all(not r["survivor_family"] for r in new["all_candidates_sorted"])
    assert new["all_candidates_sorted"][0]["desc"] == "06|word_last|rev"
    assert all(s["n_survivors_family"] == 0 for s in old["streams"])

    assert result["total_reads"] == 3556
    assert result["final_survivors"] == 0
    for gate in result["gates"]:
        assert gate["source_family_bar"] == (
            new["family_bar"] if gate["source_lane"] == new["lane"] else
            next(s["family_bar"] for s in old["streams"] if s["stream"] == gate["stream"])
        )
        assert all(p["score"] < gate["source_family_bar"] for p in gate["plants"])
        assert all(p["score"] > p["length_bar"] for p in gate["plants"] if "length_bar" in p)

    # The source's expected count is an expectation, not an upper bound.
    assert new["expected_fp_percell"] == 48 * new["fpr"]
    assert new["n_survivors_percell"] > new["expected_fp_percell"]
    print("PASS: 3,556 source reads; zero final survivors; all four planted scores below final bars")


if __name__ == "__main__":
    main()
