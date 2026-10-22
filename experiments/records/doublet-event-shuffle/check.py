"""Independent fixed-data check before trusting the permutation summaries."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
base = json.loads((ROOT / 'experiments/records/doublet-event-lags/results.json').read_text(encoding='utf-8'))
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
events = base['events']
assert len(events) == saved['event_count'] == 86
values = [event['value'] for event in events]
assert sum(saved['page_event_counts'].values()) == 86
distances = []
chosen = 0
for left, right in zip(values, values[1:]):
    clockwise = (right - left) % 29
    distance = min(clockwise, 29 - clockwise)
    distances.append(distance)
    chosen += distance in (5, 12, 14)
lag_three = sum((values[i + 3] - values[i]) % 29 == 4 for i in range(83))
assert (sum(distances), chosen, lag_three) == (734, 31, 10)
assert saved['observed']['lag_one_sum'] == 734
assert saved['observed']['lag_one_chosen_three'] == 31
assert saved['observed']['lag_three_plus4'] == 10
for control in saved['controls'].values():
    for metric in ('lag_one_sum', 'lag_one_chosen_three', 'lag_three_plus4',
                   'max_mean_numerator', 'max_directed_bin', 'max_three_circular_bins'):
        row = control[metric]
        assert row['draws'] == 20000
        assert row['monte_carlo_p'] == (row['tail_count'] + 1) / 20001
    assert sum(control['lag_one_sum_histogram'].values()) == 20000
print('Independent event recount and saved permutation-summary checks passed.')
