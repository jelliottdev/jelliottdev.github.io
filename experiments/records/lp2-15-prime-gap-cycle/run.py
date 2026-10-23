"""Test the supplied LP2-15 mod-28 gap tail against a frozen continuation."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def primes_to_index(index):
    primes = []
    candidate = 2
    while len(primes) <= index:
        prime = True
        for divisor in primes:
            if divisor * divisor > candidate:
                break
            if candidate % divisor == 0:
                prime = False
                break
        if prime:
            primes.append(candidate)
        candidate += 1
    return primes


def compute():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    source = json.loads((HERE / 'source.json').read_text(encoding='utf-8'))
    assert source['spiral_sequence'] == plan['printed_sequence']
    assert source['screenshots_sha256'] == plan['source_sha256']
    export = json.loads((ROOT / 'exports/fibonacci-prime-panel.json').read_text(encoding='utf-8'))
    page = json.loads((ROOT / 'data/pages/lp2-15.json').read_text(encoding='utf-8'))
    assert export['source_sha256'] == hashlib.sha256((ROOT / 'data/pages/lp2-15.json').read_bytes()).hexdigest()
    first = export['rows']
    assert len(first) == 16
    assert [r['prime'] for r in first] == source['spiral_sequence']
    matrix = [[None] * 4 for _ in range(4)]
    for row in first:
        r, c = row['row'] - 1, row['column'] - 1
        assert page['numbers'][r][c] == row['printed']
        matrix[r][c] = row['prime']
    assert matrix == source['derived_prime_matrix']

    fib = [0, 1]
    while fib[-1] < 46368:
        fib.append(fib[-1] + fib[-2])
    indices = list(dict.fromkeys(fib))[:24]
    assert [row['fibonacci_index'] for row in first] == indices[:16]
    assert indices[16:] == [1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368]
    all_primes = primes_to_index(indices[-1])
    seq = [all_primes[i] for i in indices]
    assert seq[:16] == source['spiral_sequence']
    gaps = [b-a for a, b in zip(seq, seq[1:])]
    mod28 = [g % 28 for g in gaps]
    mod29 = [g % 29 for g in gaps]
    assert gaps[:15] == source['shown_gaps']
    assert mod28[:15] == source['shown_mod28']
    tail = plan['claimed_cycle']
    assert tail == source['reported_tail']
    occurrences = [i + 1 for i in range(12) if mod28[i:i+4] == tail]
    predicted = tail * 2
    return {
        'fibonacci_indices': indices,
        'primes': seq,
        'gaps': gaps,
        'residues_mod28': mod28,
        'residues_mod29': mod29,
        'displayed_exact_tail_occurrences_starting_at_one': occurrences,
        'predicted_next_eight_mod28': predicted,
        'actual_next_eight_mod28': mod28[15:],
        'next_eight_matches': [a == b for a, b in zip(predicted, mod28[15:])],
        'all_eight_match': mod28[15:] == predicted,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = compute()
    encoded = (json.dumps(result, indent=2) + '\n').encode('utf-8')
    target = HERE / 'results.json'
    if args.check:
        assert target.read_bytes() == encoded, 'results.json differs from the frozen calculation'
        print('Results match the source matrix, panel construction and frozen continuation.')
    else:
        target.write_bytes(encoded)
        print(target)


if __name__ == '__main__':
    main()
