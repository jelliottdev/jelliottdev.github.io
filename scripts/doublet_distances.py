"""Reconstruct successive-doublet circular distances; no significance test."""
import argparse
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
from rune_doublets import report as doublet_report

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'exports/doublet-distances.json'


def report():
    source = doublet_report()  # Re-read the archived inputs, not cached outputs.
    alphabet = source['alphabet']
    indices = {a['rune']: i for i, a in enumerate(alphabet)}
    events = source['page']['occurrences']
    values = [indices[event['left']['rune']] for event in events]
    rows = []
    for i, (a, b) in enumerate(zip(values, values[1:])):
        directed = (b - a) % 29
        rows.append({'left_event_zero_based': i, 'right_event_zero_based': i+1,
                     'left': events[i]['left'], 'right': events[i+1]['left'],
                     'directed_difference_mod29': directed,
                     'circular_distance': min(directed, 29-directed),
                     'crosses_page': events[i]['left']['page'] != events[i+1]['left']['page']})
    counts = Counter(values)
    n = len(values)
    expectation = sum(Fraction(ca * (cb - (a == b)) * min((a-b) % 29, (b-a) % 29), n*(n-1))
                      for a, ca in counts.items() for b, cb in counts.items())
    # Independent enumeration over distinct event positions checks multiplicities.
    direct = Fraction(sum(min(abs(a-b), 29-abs(a-b))
                          for i, a in enumerate(values) for j, b in enumerate(values) if i != j), n*(n-1))
    assert direct == expectation
    observed = Fraction(sum(row['circular_distance'] for row in rows), len(rows))
    histogram = Counter(row['circular_distance'] for row in rows)
    assert sum(histogram.values()) == len(rows)
    return {'scope': 'LP2-00--55; headings included; rune-only within-page overlapping doublets. Concatenate one symbol per occurrence in page order, then compare adjacent events across page boundaries. Circular distance min(delta mod29, -delta mod29).',
            'input_sha256': source['input_sha256'], 'alphabet': alphabet,
            'event_count': n, 'pair_count': len(rows),
            'cross_page_pair_count': sum(row['crosses_page'] for row in rows),
            'distance_sum': sum(row['circular_distance'] for row in rows),
            'mean_distance': str(observed), 'mean_distance_decimal': float(observed),
            'shuffle_expected_mean': str(expectation), 'shuffle_expected_mean_decimal': float(expectation),
            'null_scope': 'Uniform permutations of the fixed extracted event multiset; expectation only. Not a shuffle of manuscript runes and not a p-value.',
            'histogram': {str(k): histogram[k] for k in range(15)}, 'pairs': rows}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--write', action='store_true')
    group.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = report()
    if args.check:
        assert result == json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: all successive-doublet distances and exact expectation reproduced')
    elif args.write:
        OUTPUT.write_text(json.dumps(result, ensure_ascii=True, indent=2)+'\n', encoding='utf-8', newline='\n')
        print('Wrote exports/doublet-distances.json')
    else:
        print(json.dumps(result, ensure_ascii=True, indent=2))
