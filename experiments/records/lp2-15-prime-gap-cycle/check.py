"""Independent sieve and source-transcription check for the LP2-15 gap tail."""
import hashlib
import json
from math import isqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def prime_sieve(limit):
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = bytes([0, 0])
    for p in range(2, isqrt(limit) + 1):
        if flags[p]:
            flags[p*p:limit+1:p] = bytes([0]) * (((limit-p*p)//p)+1)
    return [i for i, flag in enumerate(flags) if flag]


def main():
    plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
    source = json.loads((HERE / 'source.json').read_text(encoding='utf-8'))
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    page_bytes = (ROOT / 'data/pages/lp2-15.json').read_bytes()
    export = json.loads((ROOT / 'exports/fibonacci-prime-panel.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(page_bytes).hexdigest() == export['source_sha256']
    printed = json.loads(page_bytes)['numbers']
    matrix = [[None] * 4 for _ in range(4)]
    for entry in export['rows']:
        r,c = entry['row']-1,entry['column']-1
        assert printed[r][c] == entry['printed'] == abs(3301-entry['prime'])
        matrix[r][c] = entry['prime']
    assert matrix == source['derived_prime_matrix']
    fib = [0, 1]
    while fib[-1] < 46368:
        fib.append(fib[-1] + fib[-2])
    indices = list(dict.fromkeys(fib))[:24]
    assert indices == result['fibonacci_indices']
    assert [e['fibonacci_index'] for e in export['rows']] == indices[:16]
    primes = prime_sieve(result['primes'][-1])
    sequence = [primes[i] for i in indices]
    assert sequence == result['primes']
    assert sequence[:16] == source['spiral_sequence'] == plan['printed_sequence']
    gaps = [b-a for a,b in zip(sequence,sequence[1:])]
    assert gaps == result['gaps']
    assert gaps[:15] == source['shown_gaps']
    mod28 = [x%28 for x in gaps]
    mod29 = [x%29 for x in gaps]
    assert mod28 == result['residues_mod28']
    assert mod29 == result['residues_mod29']
    assert mod28[:15] == source['shown_mod28']
    tail = source['reported_tail']
    assert tail == plan['claimed_cycle'] == [8,20,10,6]
    assert [i+1 for i in range(12) if mod28[i:i+4] == tail] == result['displayed_exact_tail_occurrences_starting_at_one'] == [12]
    expected = [tail[j%4] for j in range(8)]
    assert expected == result['predicted_next_eight_mod28']
    assert mod28[15:] == result['actual_next_eight_mod28'] == [4,2,20,2,24,26,26,26]
    assert [a==b for a,b in zip(expected,mod28[15:])] == result['next_eight_matches'] == [False]*8
    assert result['all_eight_match'] is False
    print('Independent sieve, panel matrix, screenshot numerals and eight-step prediction checks passed.')


if __name__ == '__main__':
    main()
