"""Independent arithmetic and declared-bound checks on the R18 B replay."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def strip_times(value):
    if isinstance(value, dict):
        return {k: strip_times(v) for k, v in value.items()
                if k not in {'elapsed_s', 'sec_per_decode', 'sec'}}
    if isinstance(value, list):
        return [strip_times(v) for v in value]
    return value


def main():
    source = json.loads((HERE / 'source-results.json').read_text(encoding='utf-8'))
    replay = json.loads((HERE / 'replayed-results.json').read_text(encoding='utf-8'))
    gate = json.loads((HERE / 'source-gate.json').read_text(encoding='utf-8'))
    assert strip_times(source) == strip_times(replay)
    assert gate['pass'] and gate['cases'] == 24 and gate['path_mismatches'] == 0
    assert gate['max_score_delta'] < 1e-9

    s = source['supp']
    q = 1 / 29
    rho = q * s / (1 - q * s)
    assert math.isclose(rho, source['rho'], rel_tol=1e-14)
    b1 = source['B1']
    assert math.isclose(rho * 12955, b1['analytic_mean_extra_draws'], rel_tol=1e-14)
    variance = q * s / (1 - q * s) ** 2
    assert math.isclose(math.sqrt(12955 * variance), b1['analytic_sd'], rel_tol=1e-14)
    assert b1['reps'] == 200 and b1['analytic_inside_sim_ci95']
    for row in source['B2']['rows']:
        assert row['plants'] == 200
        assert math.isclose((1 - rho) ** row['L'], row['p_driftfree_analytic'], rel_tol=1e-13)
        assert 0 <= row['rigid_detect_power'] <= 1
        assert 0 <= row['beam_detect_power'] <= 1
        assert 0 <= row['rigid_mean_recovery'] <= 1
        assert 0 <= row['beam_mean_recovery'] <= 1
    assert [r['L'] for r in source['B2']['rows']] == [25, 50, 100, 120, 200, 400]
    assert [r['L'] for r in source['B3']] == [120, 400, 1000, 3000, 6000, 12956]
    for row in source['B3']:
        assert row['plants'] == 3 and row['beam_w'] == 400 and row['max_skip'] == 3
        assert row['pass'] == (row['min_score'] >= -5.5 and row['min_recovery'] >= 0.9)
        assert 0 <= row['skip_recovery_exact'] <= 1
    assert source['B3_negative_control']['wrong_key_full_length_score'] < -5.5
    print('PASS: F0 parity, full non-timing replay, drift law, six window bounds, and six planted-length gates')


if __name__ == '__main__':
    main()
