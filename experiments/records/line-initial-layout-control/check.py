"""Independent input parse, statistic check, and planted forcing control."""
from __future__ import annotations

import json
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
RUNES = "ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LOOKUP = {r: i for i, r in enumerate(RUNES)}


def main() -> None:
    result = json.loads((HERE / "results.json").read_text(encoding="utf-8"))
    raw = (HERE / "source" / "krisyotam_runes.txt").read_text(encoding="utf-8")
    # Deliberately parse percentage-delimited page strings, then slash-delimited
    # physical lines, rather than sharing run.py's streaming token parser.
    pages = []
    for page in raw.split("%"):
        lines = [[LOOKUP[c] for c in section if c in LOOKUP]
                 for section in page.split("/")]
        lines = [line for line in lines if line]
        if lines:
            pages.append(lines)
    pages = pages[:55]
    lines = [line for page in pages for line in page]
    stream = [r for line in lines for r in line]
    assert (len(pages), len(lines), len(stream)) == (55, 594, 12956)
    all_counts = np.bincount(stream, minlength=29)
    start = np.bincount([line[0] for line in lines], minlength=29)
    final = np.bincount([line[-1] for line in lines], minlength=29)
    expectation = all_counts * len(lines) / len(stream)
    observed = float(np.sum((start - expectation) ** 2 / expectation))
    terminal = float(np.sum((final - expectation) ** 2 / expectation))
    assert abs(observed - result["line_initial"]["chi2"]) < 1e-10
    assert abs(terminal - result["line_final"]["chi2"]) < 1e-10
    assert abs(observed - 78.65603328137927) < 1e-10
    assert result["line_initial"]["flat_exceedances"] == 0
    assert 0.10 < result["line_initial"]["p_layout"] < 0.30
    assert result["width_model"]["cv_fitted"] < result["width_model"]["cv_equal"]
    assert abs(result["width_model"]["chi2_size_biased"] - 38.734422839895466) < 1e-8
    assert result["width_model"]["resynced_within_one_fraction"] > .80

    replay_layout = json.loads((HERE / 'replay-layout.json').read_text(encoding='utf-8'))
    original_layout = json.loads((HERE / 'source' / 'original_confound_layout.json').read_text(encoding='utf-8'))
    assert replay_layout['T1_corr_fitted_vs_font'] is None
    for key in original_layout:
        if key != 'T1_corr_fitted_vs_font':
            compare_nested(replay_layout[key], original_layout[key])
    assert replay_layout['n_null'] == 5000

    # Construct a position-forcing signal at 60 fixed line starts. The same
    # statistic should exceed the observed typographic anomaly decisively.
    forced = start.copy()
    for line in lines[:60]:
        forced[line[0]] -= 1
        forced[28] += 1
    planted = float(np.sum((forced - expectation) ** 2 / expectation))
    assert planted > 150, planted
    assert planted > observed * 2, (planted, observed)
    check_full_grid(raw, all_counts, pages)
    print(f"PASS: {len(stream)} runes; A1 chi2={observed:.3f}, A2 chi2={terminal:.3f}; "
          f"planted A1 chi2={planted:.1f}; layout p={result['line_initial']['p_layout']:.3f}")


def check_full_grid(raw: str, full_counts: np.ndarray, pages: list[list[list[int]]]) -> None:
    """Reconstruct all ten positional sets and the two doublet-position tables."""
    values, groups = [], {name: [] for name in ('page', 'line', 'word', 'sentence')}
    positions = {'line': [], 'word': []}
    page = 0
    line = word = sentence = -1
    new_line = new_word = new_sentence = True
    line_pos = word_pos = 0
    for char in raw:
        if char == '%':
            page += 1
            new_line = new_word = new_sentence = True
            if page >= 55:
                break
        elif char == '/':
            new_line = True
        elif char in '-.':
            new_word = True
            if char == '.':
                new_sentence = True
        elif char in LOOKUP:
            if new_line:
                line += 1
                line_pos = 0
                new_line = False
            if new_word:
                word += 1
                word_pos = 0
                new_word = False
            if new_sentence:
                sentence += 1
                new_sentence = False
            values.append(LOOKUP[char])
            for name, number in (('page', page), ('line', line), ('word', word), ('sentence', sentence)):
                groups[name].append(number)
            positions['line'].append(line_pos)
            positions['word'].append(word_pos)
            line_pos += 1
            word_pos += 1
    assert len(values) == 12956
    assert (line + 1, word + 1, sentence + 1) == (594, 2928, 219)
    sets = {}
    for name in groups:
        g = np.asarray(groups[name])
        first = np.r_[0, np.flatnonzero(g[1:] != g[:-1]) + 1]
        last = np.r_[first[1:] - 1, len(g) - 1]
        sets[name] = (first, last)
    second = np.asarray([i + 1 for i, j in zip(*sets['line']) if j > i], dtype=int)
    penult = np.asarray([j - 1 for i, j in zip(*sets['line']) if j > i], dtype=int)
    subset = dict(zip(['A1_line_initial', 'A2_line_final', 'A3_word_initial',
                       'A4_word_final', 'A5_page_initial', 'A6_page_final',
                       'A7_sentence_initial', 'A8_sentence_final',
                       'A9_line_second', 'A10_line_penultimate'],
                      [sets['line'][0], sets['line'][1], sets['word'][0], sets['word'][1],
                       sets['page'][0], sets['page'][1], sets['sentence'][0],
                       sets['sentence'][1], second, penult]))
    grid = json.loads((HERE / 'replay-armA.json').read_text(encoding='utf-8'))['tests']
    original_a = json.loads((HERE / 'source' / 'original_armA.json').read_text(encoding='utf-8'))['tests']
    compare_nested(grid, original_a)
    x = np.asarray(values)
    for name, where in subset.items():
        hist = np.bincount(x[where], minlength=29)
        assert len(where) == grid[name]['n'], name
        assert hist.tolist() == grid[name]['counts'], name
        assert abs(float(np.sum((hist - full_counts * len(where) / len(x)) ** 2 /
                                (full_counts * len(where) / len(x)))) -
                   grid[name]['chi2_vs_fulltext']) < 1e-9, name
        assert grid[name]['verdict'] == ('HIT' if name == 'A1_line_initial' else 'NEGATIVE')

    c = json.loads((HERE / 'replay-armC.json').read_text(encoding='utf-8'))['tests']
    original_c = json.loads((HERE / 'source' / 'original_armC.json').read_text(encoding='utf-8'))['tests']
    compare_nested(c, original_c)
    page_of = np.asarray(groups['page'])
    pos_line = np.asarray(positions['line'])
    pos_word = np.asarray(positions['word'])
    edges = np.flatnonzero(page_of[1:] == page_of[:-1]) + 1
    repeat = x[edges] == x[edges - 1]
    line_bin = np.where(pos_line[edges] == 0, 0,
                        np.where(pos_line[edges] == 1, 1,
                                 np.where(pos_line[edges] <= 4, 2, 3)))
    word_bin = np.where(pos_word[edges] == 0, 0,
                        np.where(pos_word[edges] == 1, 1, 2))
    for name, bins, n in [('C1_doublet_rate_by_line_position', line_bin, 4),
                          ('C2_doublet_rate_by_word_position', word_bin, 3)]:
        actual = [int(np.sum(repeat[bins == b])) for b in range(n)]
        opportunities = [int(np.sum(bins == b)) for b in range(n)]
        assert actual == c[name]['doublets'], name
        assert opportunities == c[name]['transitions'], name
        assert c[name]['verdict'] == 'NEGATIVE'
    assert c['C3_suppression_boundary_vs_interior']['line_boundary']['doublets'] == 4
    assert sum(int(v) for v in repeat) == 86
    assert c['C4_difference_channel_at_line_boundary']['verdict'] == 'NEGATIVE'
    assert c['C5_MI_linefinal_to_next_lineinitial']['verdict'] == 'NEGATIVE'

    power = json.loads((HERE / 'replay-power.json').read_text(encoding='utf-8'))
    original_power = json.loads((HERE / 'source' / 'original_power.json').read_text(encoding='utf-8'))
    compare_nested(power, original_power)
    assert power['n_base'] == 200 and power['n_null'] == 2000
    for mechanism in ('M1_assign', 'M2_filter_wins'):
        curve = {row['f']: row for row in power['curve'] if row['mechanism'] == mechanism}
        assert len(curve) == 9
        assert curve[0.0]['power_D_layout'] == 0.0
        assert curve[0.0]['power_D_flat'] == 0.49
        assert curve[0.6]['power_D_layout'] == 1.0
    assert power['f80']['M1_assign/power_D_layout'] == 0.6
    assert power['f80']['M2_filter_wins/power_D_layout'] == 0.6

    bpath = HERE / 'replay-armB.json'
    assert bpath.exists(), 'The six-family source replay receipt is required'
    if bpath.exists():
        replay_b = json.loads(bpath.read_text(encoding='utf-8'))
        original_b = json.loads((HERE / 'source' / 'original_armB.json').read_text(encoding='utf-8'))
        compare_nested(replay_b['control'], original_b['control'])
        assert all(row['recovered'] for row in replay_b['control'])
        assert set(replay_b['families']) == set(original_b['families'])
        assert sum(row['n_variants'] for row in replay_b['families'].values()) == 56376
        initials = [line[0] for page_lines in pages for line in page_lines]
        diagonals = []
        for page_lines in pages:
            diagonals.extend(([line[k] for k, line in enumerate(page_lines) if k < len(line)],
                              [line[-1-k] for k, line in enumerate(page_lines) if k < len(line)]))
        families = {
            'B1_line_initial_sequence': [initials],
            'B2_per_page_acrostic': [[line[0] for line in page_lines] for page_lines in pages],
            'B3_diagonals': [row for row in diagonals if len(row) >= 4],
            'B4_every_Nth_line_initial': [initials[phase::step]
                                         for step in range(2, 13) for phase in range(step)
                                         if len(initials[phase::step]) >= 4],
            'B5_page_initial_and_final': [x[sets['page'][0]].tolist(),
                                          x[sets['page'][1]].tolist()],
            'B6_word_initial_and_final': [x[sets['word'][0]].tolist(),
                                          x[sets['word'][1]].tolist()],
        }
        for family, row in replay_b['families'].items():
            prior = original_b['families'][family]
            reads = families[family]
            assert len(reads) == row['n_reads'], family
            # Two directions, identity/Atbash, 29 shifts, and keep/drop F.
            # Drop-F variants are ineligible when fewer than four runes remain.
            n_variants = sum(116 + 58 * (sum(v != 0 for v in seq) >= 4)
                             + 58 * (sum(v != 28 for v in seq) >= 4)
                             for seq in reads if len(seq) >= 4)
            assert n_variants == row['n_variants'], (family, n_variants, row['n_variants'])
            # A larger resampling run may change null maxima; the complete
            # observed search, winner and variant count must remain identical.
            for key in ('n_reads', 'n_variants', 'best_read_index', 'best_variant',
                        'best_translit_head', 'verdict'):
                assert row[key] == prior[key], (family, key)
            assert math.isclose(row['best_score_norm'], prior['best_score_norm'],
                                rel_tol=1e-12, abs_tol=1e-12), family
            assert row['best_score_norm'] < row['null_max_max'], family


def compare_nested(a: object, b: object) -> None:
    """Compare freshly executed source outputs to the pinned source receipts."""
    if isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys()
        for key in a:
            compare_nested(a[key], b[key])
    elif isinstance(a, list):
        assert isinstance(b, list) and len(a) == len(b)
        for aa, bb in zip(a, b):
            compare_nested(aa, bb)
    elif type(a) in (int, float) and type(b) in (int, float):
        assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12) or (math.isnan(a) and math.isnan(b)), (a, b)
    else:
        assert a == b, (a, b)


if __name__ == "__main__":
    main()
