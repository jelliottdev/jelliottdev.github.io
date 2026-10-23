"""Independent scalar observed-value checks and source-table comparison."""
from collections import Counter
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / 'results.json').read_text())
    # Reconstruct bytes from the decimal integer receipt, not the producer module.
    first = result['integers'][0]
    raw = int(first['integer_decimal']).to_bytes(256, 'big')
    assert len(raw) == 256
    counts = Counter(raw)
    high, low = Counter(v // 16 for v in raw), Counter(v % 16 for v in raw)
    column = bytes(raw[r * 8 + c] for c in range(8) for r in range(32))
    observed = [len(counts), sum((counts[v] - 1) ** 2 for v in range(256)),
                sum(v.bit_count() for v in raw),
                sum((high[v] - 16) ** 2 / 16 for v in range(16)),
                sum((low[v] - 16) ** 2 / 16 for v in range(16)),
                sum(a == b for a, b in zip(raw, raw[1:])),
                sum(a == b for a, b in zip(column, column[1:]))]
    with (HERE / 'source-x1-x3.tsv').open(newline='', encoding='utf-8') as file:
        source = list(csv.DictReader(file, delimiter='\t'))
    assert len(source) == 11
    for value, saved, original in zip(observed, result['measurements'], source[:7]):
        assert value == saved['observed'] == float(original['value'])
        p = min(1., 2 * min((saved['null_at_or_below'] + 1) / 100001,
                             (saved['null_at_or_above'] + 1) / 100001))
        assert p == saved['two_sided_tail']
        assert original['detail'] == f'{p:.4g}'
        assert original['reference'] == f"null mean {saved['null_mean']:.4f}"
        assert saved['rejected_uniform_reference'] == (p < .01 / 7)
        assert original['verdict'] == ('NON-UNIFORM' if p < .01 / 7 else 'consistent')
    # Independently enumerate primes by incremental trial division.
    primes = []
    for n in range(2, 1000000):
        for q in primes:
            if q * q > n:
                break
            if n % q == 0:
                break
        else:
            primes.append(n)
            continue
        if q * q > n:
            primes.append(n)
    assert len(primes) == result['primes_checked'] == 78498
    for saved, original in zip(result['integers'], source[7:]):
        data = raw if saved['route'] == 'R' else column
        value = sum(b * 256 ** i for i, b in enumerate(data if saved['order'] == 'little' else data[::-1]))
        assert value == int(saved['integer_decimal'])
        assert value.bit_length() == saved['bit_length']
        factors = [q for q in primes if value % q == 0]
        assert factors == saved['small_prime_divisors']
        assert 3 in factors
        assert original['value'] == f'{value.bit_length()} bits'
        assert original['reference'] == 'prime=False'
        assert original['verdict'] == 'EXCLUDED as RSA modulus'
    print('PASS: scalar byte statistics, exact source tails, four integer and divisor screens')


if __name__ == '__main__':
    main()
