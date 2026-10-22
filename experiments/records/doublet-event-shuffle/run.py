"""Permutation controls for the reported LP2 doublet-event patterns."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    lag_rows = []
    for lag in (1, 2, 3):
        directed = [(b - a) % 29 for a, b in zip(values, values[lag:])]
        circular = [min(d, 29 - d) for d in directed]
        directed_counts = Counter(directed)
        circular_counts = Counter(circular)
        lag_rows.append(dict(lag=lag, pairs=len(directed), circular_sum=sum(circular),
                             plus4=directed_counts[4],
                             chosen_three=sum(circular_counts[d] for d in (5, 12, 14)),
                             largest_directed_bin=max(directed_counts.values()),
                             largest_three_circular_bins=sum(sorted(circular_counts.values(), reverse=True)[:3])))
    return dict(lag_one_sum=lag_rows[0]['circular_sum'],
                lag_one_chosen_three=lag_rows[0]['chosen_three'],
                lag_three_plus4=lag_rows[2]['plus4'],
                max_mean_numerator=max((row['circular_sum'] / row['pairs']) for row in lag_rows),
                max_directed_bin=max(row['largest_directed_bin'] for row in lag_rows),
                max_three_circular_bins=max(row['largest_three_circular_bins'] for row in lag_rows),
                lags=lag_rows)


METRICS = ('lag_one_sum', 'lag_one_chosen_three', 'lag_three_plus4',
           'max_mean_numerator', 'max_directed_bin', 'max_three_circular_bins')


def quantile(sorted_values, numerator, denominator):
    return sorted_values[min(len(sorted_values) - 1, numerator * len(sorted_values) // denominator)]


def run():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for entry in plan['inputs']:
        if digest(ROOT / entry['path']) != entry['sha256']:
            raise ValueError('Input changed: ' + entry['path'])
    source = json.loads((ROOT / plan['inputs'][0]['path']).read_text(encoding='utf-8'))
    events = source['events']
    values = [event['value'] for event in events]
    assert len(values) == 86 and all(0 <= value < 29 for value in values)
    groups = []
    for event in events:
        if not groups or groups[-1]['page'] != event['page']:
            groups.append(dict(page=event['page'], values=[]))
        groups[-1]['values'].append(event['value'])
    assert sum(map(lambda group: len(group['values']), groups)) == len(values)
    observed = stats(values)
    for old, new in zip(source['lags'], observed['lags']):
        assert old['circular_sum'] == new['circular_sum']
        assert old['plus4_count'] == new['plus4']
        assert old['distance_5_12_14_count'] == new['chosen_three']
    controls = {}
    for mode, seed_addition in (('global', 0), ('within_page', 1)):
        rng = random.Random(plan['seed'] + seed_addition)
        samples = {metric: [] for metric in METRICS}
        for _ in range(plan['draws_per_null']):
            if mode == 'global':
                shuffled = values[:]
                rng.shuffle(shuffled)
            else:
                shuffled = []
                for group in groups:
                    section = group['values'][:]
                    rng.shuffle(section)
                    shuffled.extend(section)
            trial = stats(shuffled)
            for metric in METRICS:
                samples[metric].append(trial[metric])
        controls[mode] = {}
        for metric in METRICS:
            ordered = sorted(samples[metric])
            tail = sum(value >= observed[metric] for value in ordered)
            controls[mode][metric] = dict(tail_count=tail, draws=plan['draws_per_null'],
                                          monte_carlo_p=(tail + 1) / (plan['draws_per_null'] + 1),
                                          q025=quantile(ordered, 25, 1000),
                                          median=quantile(ordered, 1, 2),
                                          q975=quantile(ordered, 975, 1000))
        controls[mode]['lag_one_sum_histogram'] = {
            str(value): count for value, count in sorted(Counter(samples['lag_one_sum']).items())
        }
    return dict(schema='liberpedia-doublet-event-shuffle-v1',
                plan_sha256=digest(HERE / 'plan.json'),
                source_sha256=digest(ROOT / plan['inputs'][0]['path']),
                event_count=len(events), page_event_counts={group['page']: len(group['values']) for group in groups},
                observed=observed, controls=controls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.check:
        if result != json.loads((HERE / 'results.json').read_text(encoding='utf-8')):
            raise SystemExit('Rerun differs from saved result')
        print('20,000 seeded shuffles per null and all six statistics reproduce.')
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as out:
            json.dump(result, out, ensure_ascii=True, separators=(',', ':'))
            out.write('\n')
    print(json.dumps({mode: {metric: row['monte_carlo_p'] for metric, row in checks.items()
                             if metric in METRICS} for mode, checks in result['controls'].items()}))


if __name__ == '__main__':
    main()
