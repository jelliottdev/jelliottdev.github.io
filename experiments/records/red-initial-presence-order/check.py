"""Independent arithmetic and second-seed check of the presence-order report."""

import csv
import hashlib
import json
from math import comb
from pathlib import Path
import random
from statistics import pvariance

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORT = HERE / 'results.json'
PLAN = HERE / 'plan.json'
CSV = ROOT / 'research/red-initials-audit.csv'


def main():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    assert report['plan_sha256'] == hashlib.sha256(PLAN.read_bytes()).hexdigest()
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
    with CSV.open(newline='', encoding='utf-8') as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 58
    selected = [i for i, row in enumerate(rows) if int(row['component_rule'])]
    source = [i for i, row in enumerate(rows) if int(row['source_total_rule'])]
    assert selected == report['corrected_pages']
    assert source == report['source_total_red_pages']
    assert set(source) - set(selected) == {7, 53}
    assert int(rows[3]['large_component_count']) == 2
    assert int(rows[33]['large_component_count']) == 2
    gaps = [b - a for a, b in zip(selected, selected[1:])]
    observed = report['observed']
    assert abs(pvariance(gaps) - observed['gap_variance']) < 1e-12
    assert selected[-1] - selected[0] == observed['span'] == 57
    longest = max(len(run) for run in ''.join('1' if i in selected else '0' for i in range(58)).split('0') if run)
    assert longest == observed['max_run'] == 2

    # Exact span count: choose two extreme pages distance s apart, then k-2
    # interior pages. Exact probability of any adjacent pair is the complement
    # of the nonadjacent 13-subsets, counted by a gap-removal bijection.
    k = len(selected)
    total = comb(58, k)
    span_numerator = sum((58 - s) * comb(s - 1, k - 2)
                         for s in range(k - 1, observed['span'] + 1))
    adjacent_numerator = total - comb(58 - k + 1, k)
    assert span_numerator == observed['span_lower_numerator'] == total
    assert adjacent_numerator == observed['max_run_upper_numerator']
    assert total == observed['denominator']
    assert sum((58 - s) * comb(s - 1, k - 2)
               for s in range(k - 1, 58)) == total
    assert report['controls']['block_span_lower_p'] == (58 - k + 1) / total
    assert report['controls']['block_max_run_upper_p'] == (58 - k + 1) / total

    # A different Monte Carlo stream checks that the gap conclusion is not a
    # peculiarity of the producer's one seeded stream.
    rng = random.Random(73107)
    lower = upper = 0
    for _ in range(100_000):
        sample = sorted(rng.sample(range(58), k))
        v = pvariance([b - a for a, b in zip(sample, sample[1:])])
        lower += v <= observed['gap_variance'] + 1e-10
        upper += v >= observed['gap_variance'] - 1e-10
    independent_lower = (lower + 1) / 100_001
    independent_upper = (upper + 1) / 100_001
    assert abs(independent_lower - observed['gap_lower_p']) < .02
    assert abs(independent_upper - observed['gap_upper_p']) < .02
    receipt = {
        'schema': 'liberpedia-red-initial-presence-order-check-v1',
        'results_sha256': hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        'exact_span_lower_numerator': span_numerator,
        'exact_adjacent_upper_numerator': adjacent_numerator,
        'exact_denominator': total,
        'independent_seed': 73107,
        'independent_trials': 100_000,
        'independent_gap_lower_p': independent_lower,
        'independent_gap_upper_p': independent_upper,
    }
    (HERE / 'check.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print('PASS: independent page inventory, exact span/adjacency counts and second-seed spacing tails')


if __name__ == '__main__':
    main()
