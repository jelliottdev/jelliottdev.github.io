"""Independent source-output arithmetic and model-consistency audit for R18 C."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = 29
L = 12956


def close(a, b):
    assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10), (a, b)


def main():
    source = json.loads((HERE / 'source-results.json').read_text(encoding='utf-8'))
    replay = json.loads((HERE / 'replayed-results.json').read_text(encoding='utf-8'))
    assert source == replay
    r = 86 / 12955
    q = 1 / N
    s = 0.8129
    hc = source['H_C']
    row = -r * math.log2(r) - (1 - r) * math.log2((1 - r) / (N - 1))
    close(hc['unfiltered_bits'], L * math.log2(N))
    close(hc['row_entropy_bits'], row)
    close(hc['filtered_bits'], math.log2(N) + (L - 1) * row)
    close(hc['filter_information_injection_bits'], hc['unfiltered_bits'] - hc['filtered_bits'])
    close(hc['bits_per_symbol_removed'], hc['filter_information_injection_bits'] / L)
    hp = source['H_P']
    best = min(hp['by_order'], key=lambda x: x['bits_per_rune'])
    assert [x['order'] for x in hp['by_order']] == list(range(6))
    assert hp['best_order'] == best['order'] == 3
    close(hp['bits_per_rune'], best['bits_per_rune'])
    close(hp['total_bits'], best['bits_per_rune'] * L)
    ac = source['acceptance_channel']
    close(ac['closed_form_residual_rate'], (1 - s) / (N - s))
    close(ac['observed_residual_rate'], r)
    assert ac['mc_reps_per_arm'] == 1000
    assert ac['plaintext_information_bits'] == 0
    rho = q * s / (1 - q * s)
    close(source['rho'], rho)
    expected_pad_bits = (L + rho * L) * math.log2(N)
    budgets = source['budgets']
    assert len(budgets) == 5
    close(budgets[0]['H_K_bits'], expected_pad_bits)
    assert [b['H_K_bits'] for b in budgets[1:]] == [40, 256, 64, 32]
    for budget in budgets:
        close(budget['H_P_bits'], hp['total_bits'])
        close(budget['H_C_bits'], hc['filtered_bits'])
        close(budget['deficit_bits'], budget['H_P_bits'] + budget['H_K_bits'] - budget['H_C_bits'])
        assert budget['determined'] == (budget['deficit_bits'] <= 0)
    close(source['max_H_K_for_determinacy_bits'], hc['filtered_bits'] - hp['total_bits'])
    for item in source['sensitivity_to_H_P']:
        close(item['H_P_bits'], item['bits_per_rune'] * L)
        close(item['max_H_K_for_determinacy_bits'], hc['filtered_bits'] - item['H_P_bits'])
        close(item['full_pad_deficit_bits'], item['H_P_bits'] + expected_pad_bits - hc['filtered_bits'])
    # In a *deterministic* low-seed model with no omitted random coins,
    # H(C) cannot exceed H(P,seed) <= H(P)+H(seed). The source uses its
    # full-uniform-pad H(C) unchanged in those rows. These positive shortfalls
    # expose the model-mixing; they do not estimate LP2's true entropy.
    shortfalls = [b['H_C_bits'] - b['H_P_bits'] - b['H_K_bits'] for b in budgets[1:]]
    assert all(x > 29000 for x in shortfalls)
    print('PASS: exact source replay, entropy and sensitivity arithmetic, 29k-bit conditional model mismatch')


if __name__ == '__main__':
    main()
