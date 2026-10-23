"""Independently recount manuscript statistics in the R18 source-run receipt.

This checks observations and analytic arithmetic, not the source classifier's power.
"""
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'


def finite_json(value):
    """The internal receipt represents the source's Infinity values as null."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: finite_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [finite_json(item) for item in value]
    return value


def main():
    receipt = json.loads(Path(__file__).with_name('results.json').read_text(encoding='utf-8'))
    source = receipt['source_results']
    runes = []
    for page in range(56):
        text = (ROOT / 'text' / f'lp2-{page:02d}.txt').read_text(encoding='utf-8')
        runes.extend(RUNES.index(c) for c in text if c in RUNES)
    n = len(runes)
    assert n == source['n'] == 12956
    measured = {}
    lag_counts = {}
    for lag in range(1, 9):
        count = sum(a == b for a, b in zip(runes, runes[lag:]))
        lag_counts[lag] = count
        pairs = n - lag
        measured[f'lag{lag}_rate'] = count / pairs
        measured[f'lag{lag}_z'] = (count - pairs / 29) / math.sqrt(pairs * 28 / 841)
    pairs = sum(n - lag for lag in range(2, 9))
    matches = sum(lag_counts[lag] for lag in range(2, 9))
    measured['bleed28_rate'] = matches / pairs
    measured['bleed28_z'] = (matches - pairs / 29) / math.sqrt(pairs * 28 / 841)
    differences = Counter((b - a) % 29 for a, b in zip(runes, runes[1:]))
    expected = sum(differences[i] for i in range(1, 29)) / 28
    deviations = [(differences[i] - expected) / math.sqrt(expected * 27 / 28)
                  for i in range(1, 29)]
    measured['delta_chi2'] = sum((differences[i] - expected) ** 2 / expected
                                 for i in range(1, 29))
    measured['delta_chi2_df'] = measured['delta_chi2'] / 27
    measured['max_abs_delta_z'] = max(map(abs, deviations))
    measured['argmax_delta'] = max(range(1, 29), key=lambda i: abs(deviations[i - 1]))
    measured['delta0_count'] = differences[0]
    measured['run2'] = lag_counts[1]
    measured['run3'] = sum(a == b == c for a, b, c in zip(runes, runes[1:], runes[2:]))
    measured['abab'] = sum(a == c and b == d and a != b
                           for a, b, c, d in zip(runes, runes[1:], runes[2:], runes[3:]))
    measured['abab_z'] = (measured['abab'] - (n - 3) / 841) / math.sqrt(
        (n - 3) * (1 / 841) * (840 / 841))
    assert set(measured) == set(source['real'])
    for name, actual in measured.items():
        assert math.isclose(actual, source['real'][name], rel_tol=1e-11, abs_tol=1e-11), name
    rate = measured['lag1_rate']
    suppression = (1 - 29 * rate) / (1 - rate)
    extra_draws = n * suppression / (29 - suppression)
    assert math.isclose(suppression, source['analytic']['s_star'], rel_tol=1e-12)
    assert math.isclose(extra_draws, source['analytic']['expected_extra_draws'], rel_tol=1e-12)
    assert receipt['execution']['non_timing_fields_match'] is True
    original = json.loads(Path(__file__).with_name('source-output-raw.txt').read_text(encoding='utf-8'))
    replayed = json.loads(Path(__file__).with_name('replayed-output-raw.txt').read_text(encoding='utf-8'))
    assert finite_json(original) == json.loads(Path(__file__).with_name('source-results.json').read_text(encoding='utf-8'))
    assert finite_json(replayed) == json.loads(Path(__file__).with_name('replayed-results.json').read_text(encoding='utf-8'))
    assert source == finite_json({k: v for k, v in original.items() if k != 'elapsed_s'})
    assert {k: v for k, v in replayed.items() if k != 'elapsed_s'} == \
           {k: v for k, v in original.items() if k != 'elapsed_s'}
    print(f'PASS: {len(measured)} manuscript statistics and conditional draw-count arithmetic; '
          'simulation power remains a separate source claim.')


if __name__ == '__main__':
    main()
