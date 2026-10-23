"""Independent A1/A2 and T1–T3 measurement for the full C-02 source replay.

The other 19 source cases and planted-power curve are retained in separate
source-run receipts and checked by check.py against an independent input parse.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
INDEX = {c: i for i, c in enumerate(RUNES)}
N = len(RUNES)
SEPS = {"-": 29, ".": 30}


def read_lines() -> list[tuple[int, list[int]]]:
    source = (HERE / "source" / "krisyotam_runes.txt").read_text(encoding="utf-8")
    lines: list[tuple[int, list[int]]] = []
    page = 0
    current: list[int] = []
    for char in source:
        if char == "%":
            if current:
                lines.append((page, current))
                current = []
            page += 1
            if page >= 55:
                break
        elif char == "/":
            lines.append((page, current))
            current = []
        elif char in INDEX:
            current.append(INDEX[char])
        elif char in SEPS:
            current.append(SEPS[char])
    return [(page, row) for page, row in lines if any(x < N for x in row)]


def counts(rows: list[tuple[int, list[int]]]) -> np.ndarray:
    matrix = np.zeros((len(rows), 31), dtype=float)
    for j, (_, row) in enumerate(rows):
        for token in row:
            matrix[j, token] += 1
    return matrix


def full_mask(rows: list[tuple[int, list[int]]]) -> np.ndarray:
    return np.array([i + 1 < len(rows) and rows[i + 1][0] == p
                     for i, (p, _) in enumerate(rows)], dtype=bool)


def fit_widths(matrix: np.ndarray, selected: np.ndarray) -> np.ndarray:
    m = matrix[selected]
    return np.linalg.solve(m.T @ m + 0.001 * np.eye(31), m.T @ np.ones(len(m)))


def chi(count: np.ndarray, whole: np.ndarray, size: int) -> float:
    exp = whole / whole.sum() * size
    return float(np.sum((count - exp) ** 2 / exp))


def reflow(tokens: np.ndarray, widths: np.ndarray, budget: float) -> list[list[int]]:
    output: list[list[int]] = []
    current: list[int] = []
    used = 0.0
    for value in tokens:
        t = int(value)
        if current and used + widths[t] > budget:
            output.append(current)
            current = []
            used = 0.0
        current.append(t)
        used += widths[t]
    if current:
        output.append(current)
    return output


def edges(rows: list[list[int]]) -> tuple[np.ndarray, np.ndarray]:
    first, last = [], []
    for row in rows:
        runes = [x for x in row if x < N]
        if runes:
            first.append(runes[0])
            last.append(runes[-1])
    return np.asarray(first, dtype=int), np.asarray(last, dtype=int)


def main() -> None:
    rows = read_lines()
    assert len(rows) == 594
    pages = {p for p, _ in rows}
    assert len(pages) == 55
    stream = np.asarray([x for _, row in rows for x in row if x < N], dtype=int)
    assert len(stream) == 12956
    histogram = np.bincount(stream, minlength=N)
    real = [row for _, row in rows]
    initial, final = edges(real)
    assert len(initial) == len(final) == 594
    obs_initial = chi(np.bincount(initial, minlength=N), histogram, len(initial))
    obs_final = chi(np.bincount(final, minlength=N), histogram, len(final))

    matrix = counts(rows)
    mask = full_mask(rows)
    assert int(mask.sum()) == 539
    widths = fit_widths(matrix, mask)
    totals = matrix[mask] @ widths
    equal_totals = matrix[mask].sum(axis=1)
    cv_fit = float(totals.std() / totals.mean())
    cv_equal = float(equal_totals.std() / equal_totals.mean())
    rel_widths = widths[:N] / widths[:N].mean()
    excess = np.log((np.bincount(initial, minlength=N) + .5) /
                    (histogram / histogram.sum() * len(initial) + .5))
    corr = float(np.corrcoef(rel_widths, excess)[0, 1])
    size_bias = histogram * widths[:N]
    size_bias = size_bias / size_bias.sum() * len(initial)
    chi_size_bias = float(np.sum((np.bincount(initial, minlength=N) - size_bias) ** 2 / size_bias))

    all_tokens = np.asarray([x for row in real for x in row], dtype=np.int16)
    median_budget = float(np.median(totals))
    trials = [(abs(len(lines) - 594), float(b), lines)
              for b in np.linspace(median_budget * .9, median_budget * 1.1, 201)
              if (lines := reflow(all_tokens, widths, float(b)))]
    _, budget, predicted = min(trials, key=lambda z: z[0])
    assert len(predicted) in (594, 595)
    errors = []
    offset = 0
    for row in real:
        used = 0.0
        length = 0
        for token in all_tokens[offset:]:
            if length and used + widths[token] > budget:
                break
            used += widths[token]
            length += 1
        errors.append(length - len(row))
        offset += len(row)

    rng = np.random.default_rng(3301)
    n_flat = 100000
    flat_draws = rng.multivariate_hypergeometric(histogram, len(initial), size=n_flat)
    expected = histogram / histogram.sum() * len(initial)
    flat_chi = np.sum((flat_draws - expected) ** 2 / expected, axis=1)
    flat_hits = int(np.count_nonzero(flat_chi >= obs_initial))

    # New, declared seed for the reflow control. Shuffle only runes; punctuation
    # stays at the original token positions. Widths and budget remain frozen.
    n_layout = 2000
    layout_rng = np.random.default_rng(91033)
    rune_positions = np.flatnonzero(all_tokens < N)
    layout_initial = np.empty(n_layout)
    layout_final = np.empty(n_layout)
    for trial in range(n_layout):
        shuffled = all_tokens.copy()
        values = shuffled[rune_positions].copy()
        layout_rng.shuffle(values)
        shuffled[rune_positions] = values
        first, last = edges(reflow(shuffled, widths, budget))
        layout_initial[trial] = chi(np.bincount(first, minlength=N), histogram, len(first))
        layout_final[trial] = chi(np.bincount(last, minlength=N), histogram, len(last))

    output = {
        "pages": 55, "lines": 594, "width_limited_lines": 539, "runes": len(stream),
        "flat_null_draws": n_flat, "layout_null_draws": n_layout,
        "line_initial": {"chi2": obs_initial, "flat_exceedances": flat_hits,
                         "p_flat": (flat_hits + 1) / (n_flat + 1),
                         "layout_exceedances": int(np.count_nonzero(layout_initial >= obs_initial)),
                         "p_layout": float((np.count_nonzero(layout_initial >= obs_initial) + 1) / (n_layout + 1)),
                         "layout_mean": float(layout_initial.mean()),
                         "layout_p95": float(np.quantile(layout_initial, .95))},
        "line_final": {"chi2": obs_final,
                       "p_layout": float((np.count_nonzero(layout_final >= obs_final) + 1) / (n_layout + 1))},
        "width_model": {"cv_equal": cv_equal, "cv_fitted": cv_fit,
                        "correlation_with_initial_excess": corr,
                        "chi2_size_biased": chi_size_bias,
                        "relative_widths": {r: float(w) for r, w in zip(RUNES, rel_widths)},
                        "reflow_budget": budget, "reflow_lines": len(predicted),
                        "resynced_exact_fraction": float(np.mean(np.asarray(errors) == 0)),
                        "resynced_within_one_fraction": float(np.mean(np.abs(errors) <= 1))},
        "source_comparison": {"source_flat_chi2": 78.65603328137927,
                              "source_layout_p_5000": 0.1765646870625875,
                              "source_external_font_correlation_unverified": 0.8791432674755318},
    }
    (HERE / "results.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8", newline="\n")
    print(json.dumps({"A1": output["line_initial"], "width": {k: v for k, v in output["width_model"].items() if k != "relative_widths"}}, indent=2))


if __name__ == "__main__":
    main()
