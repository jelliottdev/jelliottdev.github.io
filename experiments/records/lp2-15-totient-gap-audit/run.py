"""Audit the reported LP2-15 totient/prime-gap arrays without fitting a rune key."""
import argparse
import hashlib
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_prime(n):
    return n >= 2 and all(n % d for d in range(2, isqrt(n) + 1))


def phi(n):
    result, remainder = n, n
    for divisor in range(2, isqrt(n) + 1):
        if remainder % divisor:
            continue
        result -= result // divisor
        while remainder % divisor == 0:
            remainder //= divisor
    if remainder > 1:
        result -= result // remainder
    return result


def primes_through(n):
    return [candidate for candidate in range(2, n + 1) if is_prime(candidate)]


def fibonacci_through(n):
    # Distinct nonnegative Fibonacci values; the repeated initial 1 is a
    # separate representation issue, not an alternative integer value.
    values = [0, 1]
    while values[-1] < n:
        values.append(values[-1] + values[-2])
    return values


def compute():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    for source in plan['inputs']:
        assert sha(ROOT / source['path']) == source['sha256'], source['path']
    page = json.loads((ROOT / 'data/pages/lp2-15.json').read_text(encoding='utf-8'))
    printed = page['numbers']
    source = plan['source_arrays']
    assert len(printed) == 4 and all(len(row) == 4 for row in printed)
    assert all(len(rows) == 4 and all(len(row) == 4 for row in rows)
               for rows in (source['post_totient'], source['prime_candidates'], source['fibonacci_gaps']))
    max_candidate = max(3301 + x for row in printed for x in row)
    prime_list = primes_through(max_candidate)
    ordinal = {p: i for i, p in enumerate(prime_list)}
    fibs = fibonacci_through(len(prime_list))
    fib_set = set(fibs)
    cells = []
    for r in range(4):
        for c in range(4):
            n = printed[r][c]
            transformed = phi(n) if is_prime(n) else n
            reported_transformed = source['post_totient'][r][c]
            reported_candidate = source['prime_candidates'][r][c]
            reported_gap = source['fibonacci_gaps'][r][c]
            signs = []
            for sign, candidate in (('-', 3301 - transformed), ('+', 3301 + transformed)):
                candidate_is_prime = is_prime(candidate)
                index = ordinal.get(candidate)
                signs.append({
                    'sign': sign, 'candidate': candidate,
                    'prime': candidate_is_prime,
                    'zero_based_prime_index': index,
                    'fibonacci_index': index in fib_set if index is not None else False,
                    'source_selected': candidate == reported_candidate,
                })
            index = ordinal.get(reported_candidate)
            if index is None or index not in fib_set:
                previous_distinct_gap = None
            elif index == 0:
                previous_distinct_gap = None
            else:
                previous_distinct_gap = index - fibs[fibs.index(index) - 1]
            # The canonical 0,1,1,2... series makes the predecessor of 1
            # occurrence-dependent. The source does not assign its two 3s
            # to distinct occurrences of that repeated 1.
            compatible_gaps = [0, 1] if index == 1 else (
                [] if previous_distinct_gap is None else [previous_distinct_gap])
            cells.append({
                'row': r + 1, 'column': c + 1, 'printed': n,
                'printed_is_prime': is_prime(n),
                'calculated_post_totient': transformed,
                'source_post_totient': reported_transformed,
                'post_totient_matches': transformed == reported_transformed,
                'sign_options': signs,
                'source_prime_candidate': reported_candidate,
                'source_candidate_matches_one_sign': any(s['source_selected'] for s in signs),
                'source_candidate_prime_index': index,
                'source_index_is_fibonacci': index in fib_set if index is not None else False,
                'source_gap': reported_gap,
                'predecessor_gap_options': compatible_gaps,
                'source_gap_matches': None if reported_gap is None else reported_gap in compatible_gaps,
            })
    specified = [cell for cell in cells if cell['source_gap'] is not None]
    return {
        'schema': 'liberpedia-lp2-15-totient-gap-audit-v1',
        'plan_sha256': sha(HERE / 'plan.json'),
        'page': page['id'], 'image_sha256': page['image_sha256'],
        'printed_matrix': printed,
        'calculated_post_totient': [[cells[4*r+c]['calculated_post_totient'] for c in range(4)] for r in range(4)],
        'source_prime_candidates': source['prime_candidates'],
        'calculated_prime_indices': [[cells[4*r+c]['source_candidate_prime_index'] for c in range(4)] for r in range(4)],
        'source_fibonacci_gaps': source['fibonacci_gaps'],
        'cells': cells,
        'summary': {
            'printed_prime_cells': sum(cell['printed_is_prime'] for cell in cells),
            'post_totient_matches': sum(cell['post_totient_matches'] for cell in cells),
            'source_candidate_sign_matches': sum(cell['source_candidate_matches_one_sign'] for cell in cells),
            'source_fibonacci_indices': sum(cell['source_index_is_fibonacci'] for cell in cells),
            'source_plus_cells': [[cell['row'], cell['column']] for cell in cells
                                  if any(s['source_selected'] and s['sign'] == '+' for s in cell['sign_options'])],
            'primality_ambiguous_cells': [[cell['row'], cell['column']] for cell in cells
                                          if sum(s['prime'] for s in cell['sign_options']) > 1],
            'prime_and_fibonacci_index_ambiguous_cells': [[cell['row'], cell['column']] for cell in cells
                if sum(s['prime'] and s['fibonacci_index'] for s in cell['sign_options']) > 1],
            'source_gap_specified': len(specified),
            'source_gap_matches': sum(cell['source_gap_matches'] for cell in specified),
            'source_gap_mismatches': [[cell['row'], cell['column'], cell['source_gap'], cell['predecessor_gap_options']]
                                      for cell in specified if not cell['source_gap_matches']],
            'source_gap_question_marks': [[cell['row'], cell['column']] for cell in cells if cell['source_gap'] is None],
            'duplicate_source_prime_index': 1,
            'missing_prime_index_zero': all(cell['source_candidate_prime_index'] != 0 for cell in cells),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true')
    group.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = compute()
    if args.check:
        assert result == json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    else:
        with args.output.open('x', encoding='utf-8', newline='\n') as handle:
            json.dump(result, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
    print(result['summary'])


if __name__ == '__main__':
    main()
