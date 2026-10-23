"""Cross-check the manuscript measurements and homophonic optimum by separate recurrences."""

from __future__ import annotations

from collections import Counter
import json
import math
from pathlib import Path

from run import ROOT, HERE, site_inputs, report


def allocation_dp(q: list[float], n: int) -> float:
    """Minimum χ² by dynamic programming, independent of multiset enumeration."""
    used = [rate for rate in q if rate]
    expected = n / 29
    costs = {0: 0.0}
    for rate in used:
        next_costs = {}
        for already, cost in costs.items():
            for symbols in range(1, 30 - already):
                total = already + symbols
                if total > 29:
                    continue
                candidate = cost + symbols * (n * rate / symbols - expected) ** 2 / expected
                next_costs[total] = min(next_costs.get(total, math.inf), candidate)
        costs = next_costs
    return min(cost + (29 - allocated) * expected for allocated, cost in costs.items())


def marker_fixture() -> None:
    plain = [0, 3, 7, 3, 2, 3, 8, 4, 3, 1]
    marker = 3
    key = [1, 2, 4, 7, 8, 10, 3, 6, 5, 11]  # all nonzero mod 29
    cipher = [12]
    for p, k in zip(plain[1:], key[1:]):
        cipher.append((cipher[-1] + (p - marker) * k) % 29)
    assert [i for i, (a, b) in enumerate(zip(cipher, cipher[1:]), 1) if a == b] == [i for i, p in enumerate(plain) if i and p == marker]


def main() -> None:
    saved = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    if saved != report():
        raise AssertionError("site inputs/results changed")
    labels, words, sections, _ = site_inputs()
    plain = [r for w in words for r in w]
    q = [plain.count(i) / len(plain) for i in range(29)]
    dp = allocation_dp(q, saved["lp2_runes"])
    if not math.isclose(dp, saved["C15"]["minimum_expected_chi2"], abs_tol=1e-8):
        raise AssertionError((dp, saved["C15"]["minimum_expected_chi2"]))
    flat = allocation_dp([1 / 29] * 29, saved["lp2_runes"])
    controlled = allocation_dp([2 / 29] * 3 + [1 / 29] * 23 + [0] * 3, saved["lp2_runes"])
    assert math.isclose(flat, 0.0, abs_tol=1e-9) and math.isclose(controlled, 0.0, abs_tol=1e-9)
    marker_fixture()

    assert saved["C3"]["count_compatible"] == ["NG", "IA", "EA"]
    assert saved["C3"]["excluded_under_source_rule"] == 29
    assert saved["doublet_word_classes"] == {"initial": 23, "medial": 44, "final": 19, "sole": 0}
    assert saved["lp2_pair_opportunities"] == 12947
    assert saved["lp2_doublets"] == 86
    assert math.isclose(saved["C15"]["observed_lp2_chi2"], 26.361685705464648, abs_tol=1e-9)
    assert math.isclose(dp, 4802.036755067442, abs_tol=1e-8)
    # Source test run checks its own planted unit controls and both original verdicts.
    source = (HERE / "source-tests.txt").read_text(encoding="utf-8")
    assert "Ran 6 tests" in source and source.rstrip().endswith("OK")
    assert source.count(" ... ok") == 6
    print("PASS: site corpus, 29 marker checks, separate homophone DP and six source tests")


if __name__ == "__main__":
    main()
