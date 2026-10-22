"""Independent sieve and divisor-count check of the LP2-15 source-array audit."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def sieve(limit):
    flags = [False, False] + [True] * (limit - 1)
    for value in range(2, int(limit ** .5) + 1):
        if flags[value]:
            flags[value * value:limit + 1:value] = [False] * len(range(value * value, limit + 1, value))
    return flags


def totient_by_gcd(n):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    return sum(gcd(k, n) == 1 for k in range(1, n + 1))


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    page_path = ROOT / 'data/pages/lp2-15.json'
    assert hashlib.sha256(page_path.read_bytes()).hexdigest() == plan['inputs'][0]['sha256']
    page = json.loads(page_path.read_text(encoding='utf-8'))
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    source = plan['source_arrays']
    assert saved['printed_matrix'] == page['numbers']
    assert saved['source_prime_candidates'] == source['prime_candidates']
    assert saved['source_fibonacci_gaps'] == source['fibonacci_gaps']
    assert len(saved['cells']) == 16
    flags = sieve(3301 + max(max(row) for row in page['numbers']))
    primes = [value for value, flag in enumerate(flags) if flag]
    ranks = {value: rank for rank, value in enumerate(primes)}
    fibs = [0, 1]
    while fibs[-1] < len(primes):
        fibs.append(fibs[-1] + fibs[-2])
    assert sorted(ranks[x] for row in source['prime_candidates'] for x in row) == [
        1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]
    for r in range(4):
        for c in range(4):
            cell = saved['cells'][4 * r + c]
            number = page['numbers'][r][c]
            transformed = totient_by_gcd(number) if flags[number] else number
            candidate = source['prime_candidates'][r][c]
            rank = ranks[candidate]
            assert (cell['row'], cell['column'], cell['printed']) == (r+1, c+1, number)
            assert cell['printed_is_prime'] == flags[number]
            assert cell['calculated_post_totient'] == transformed == source['post_totient'][r][c]
            assert cell['source_candidate_prime_index'] == rank == saved['calculated_prime_indices'][r][c]
            assert cell['source_index_is_fibonacci'] == (rank in fibs)
            choices = [('−', 3301-transformed), ('+', 3301+transformed)]
            assert len(cell['sign_options']) == 2
            for option, (sign, value) in zip(cell['sign_options'], choices):
                assert option['sign'] == ('-' if sign == '−' else '+')
                assert option['candidate'] == value
                assert option['prime'] == (value >= 2 and flags[value])
                assert option['source_selected'] == (value == candidate)
                assert option['zero_based_prime_index'] == ranks.get(value)
                assert option['fibonacci_index'] == (ranks.get(value) in fibs)
            assert cell['source_candidate_matches_one_sign'] == (candidate in [value for _, value in choices])
            gap = source['fibonacci_gaps'][r][c]
            if rank == 1:
                admissible = [0, 1]
            elif rank in fibs and rank > 1:
                admissible = [rank-fibs[fibs.index(rank)-1]]
            else:
                admissible = []
            assert cell['predecessor_gap_options'] == admissible
            assert cell['source_gap_matches'] == (None if gap is None else gap in admissible)
    summary = saved['summary']
    assert summary['printed_prime_cells'] == 1
    assert summary['post_totient_matches'] == 16
    assert summary['source_candidate_sign_matches'] == 16
    assert summary['source_fibonacci_indices'] == 16
    assert summary['source_plus_cells'] == [[4, 1], [4, 2]]
    assert summary['primality_ambiguous_cells'] == [[2, 2], [2, 3]]
    assert summary['prime_and_fibonacci_index_ambiguous_cells'] == []
    assert summary['source_gap_specified'] == 15
    assert summary['source_gap_matches'] == 14
    assert summary['source_gap_mismatches'] == [[4, 1, 317, [377]]]
    assert summary['source_gap_question_marks'] == [[2, 2]]
    assert summary['missing_prime_index_zero'] is True
    print('Independent gcd-totient, sieve, sign, prime-rank and gap checks passed.')


if __name__ == '__main__':
    main()
