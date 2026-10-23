"""Independent observable measurements for the pinned D-01 filter comparison.

This script does not import the source experiment's parser, statistics or
generators. It verifies the input geometry and core measured quantities before
the source's calibrated simulation results are considered.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LOOKUP = {c: i for i, c in enumerate(RUNES)}
N = 29


def pages_and_lines() -> list[list[list[int]]]:
    raw = (HERE / "source" / "krisyotam_runes.txt").read_text(encoding="utf-8")
    nonempty = [segment for segment in raw.split("%")
                if any(char in LOOKUP for char in segment)]
    pages: list[list[list[int]]] = []
    for segment in nonempty[:55]:
        pages.append([[LOOKUP[c] for c in line if c in LOOKUP]
                      for line in segment.split("/")])
    return pages


def window_balance(x: list[int], width: int, probs: list[float]) -> float:
    count_windows = len(x) // width
    total = 0.0
    for window in range(count_windows):
        row = [0] * N
        for value in x[window * width:(window + 1) * width]:
            row[value] += 1
        total += sum((actual - width * p) ** 2 / (width * p)
                     for actual, p in zip(row, probs))
    return total / count_windows / (N - 1)


def main() -> None:
    pages = pages_and_lines()
    x = [v for page in pages for line in page for v in line]
    assert len(pages) == 55 and len(x) == 12956
    nonempty_lines = sum(bool(line) for page in pages for line in page)
    line_slots = sum(len(page) for page in pages)
    # The source's global line ordinal increments on each slash and page
    # turn; a trailing empty slot has no rune and does not affect max+1.
    occupied_line_ordinals = []
    ordinal = 0
    page_of = []
    line_of = []
    for page_num, page in enumerate(pages):
        for line in page:
            for _ in line:
                occupied_line_ordinals.append(ordinal)
                page_of.append(page_num)
                line_of.append(ordinal)
            ordinal += 1
    assert nonempty_lines == 594 and line_slots == 649
    assert max(occupied_line_ordinals) + 1 == 648

    n = len(x)
    hist = [x.count(i) for i in range(N)]
    probs = [count / n for count in hist]
    lag_equal = {lag: sum(x[i] == x[i-lag] for i in range(lag, n))
                 for lag in range(1, 9)}
    lag_rates = {f"lag{lag}": lag_equal[lag] / (n-lag) for lag in lag_equal}
    pooled_success = sum(lag_equal[lag] for lag in range(2, 9))
    pooled_trials = sum(n-lag for lag in range(2, 9))
    chance = 1 / N
    bleed_z = ((pooled_success - pooled_trials * chance) /
               math.sqrt(pooled_trials * chance * (1-chance)))
    repeat_indices = [i for i in range(1, n) if x[i] == x[i-1]]
    cross_lines = sum(line_of[i] != line_of[i-1] for i in repeat_indices)
    cross_pages = sum(page_of[i] != page_of[i-1] for i in repeat_indices)
    previous: dict[int, int] = {}
    gaps = []
    for i, symbol in enumerate(x):
        if symbol in previous:
            gaps.append(i - previous[symbol])
        previous[symbol] = i
    gap_mean = sum(gaps) / len(gaps)
    gap_cv = math.sqrt(sum((g-gap_mean)**2 for g in gaps) / len(gaps)) / gap_mean

    page_opportunities = [len([v for line in page for v in line])-1 for page in pages]
    page_doublets = [sum(linear[i] == linear[i-1] for i in range(1, len(linear)))
                     for page in pages
                     for linear in [[v for line in page for v in line]]]
    rate = sum(page_doublets) / sum(page_opportunities)
    dispersion = (sum((obs - m*rate)**2 / (m*rate*(1-rate))
                      for obs, m in zip(page_doublets, page_opportunities))
                  / (len(pages)-1))

    results = {
        "pages": len(pages),
        "runes": n,
        "nonempty_physical_lines": nonempty_lines,
        "slash_delimited_slots": line_slots,
        "source_occupied_line_ordinals": max(occupied_line_ordinals)+1,
        "doublets": len(repeat_indices),
        "doublets_across_lines": cross_lines,
        "doublets_across_pages": cross_pages,
        "lag_equal_counts": lag_equal,
        "lag_rates": lag_rates,
        "lag2_to_8_rate": pooled_success / pooled_trials,
        "lag2_to_8_z": bleed_z,
        "gap_cv": gap_cv,
        "window_chi2_over_df": {str(w): window_balance(x, w, probs)
                                for w in (29, 58, 116, 290)},
        "page_doublet_dispersion": dispersion,
    }
    (HERE / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2)+"\n",
        encoding="utf-8", newline="\n")
    print(f"{n} runes; {len(repeat_indices)} repeats; {cross_lines} cross line slots; "
          f"W58 chi2/df {results['window_chi2_over_df']['58']:.4f}")


if __name__ == "__main__":
    main()
