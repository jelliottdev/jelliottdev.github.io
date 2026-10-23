"""Independent raw-grid measurements and exact small-prime divisibility tests."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx'
NAMES = ('distinct values', 'chi2 256 bins', 'ones in 2048 bits',
         'high-nibble chi2', 'low-nibble chi2', 'adjacent equal R', 'adjacent equal C')


def grid_bytes():
    plan = json.loads((HERE / 'plan.json').read_text())
    path = ROOT / plan['input']['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == plan['input']['sha256']
    with path.open(encoding='utf-8', newline='') as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 256
    assert [int(row['sequence']) for row in rows] == list(range(1, 257))
    values = [60 * DIGITS.index(row['token'][0]) + DIGITS.index(row['token'][1]) for row in rows]
    assert all(0 <= v < 256 for v in values)
    return bytes(values)


def measures(blocks):
    """Vectorized counts; no import from the proposed source's implementation."""
    rows = blocks.shape[0]
    labels = np.arange(rows, dtype=np.int64)[:, None]
    def counts(values, alphabet):
        tagged = values.astype(np.int64) + alphabet * labels
        return np.bincount(tagged.ravel(), minlength=rows * alphabet).reshape(rows, alphabet)
    whole, high, low = counts(blocks, 256), counts(blocks >> 4, 16), counts(blocks & 15, 16)
    column_order = blocks.reshape(rows, 32, 8).transpose(0, 2, 1).reshape(rows, 256)
    return np.stack(((whole != 0).sum(1), ((whole - 1) ** 2).sum(1),
                     np.unpackbits(blocks, axis=1).sum(1),
                     ((high - 16) ** 2).sum(1) / 16,
                     ((low - 16) ** 2).sum(1) / 16,
                     (blocks[:, 1:] == blocks[:, :-1]).sum(1),
                     (column_order[:, 1:] == column_order[:, :-1]).sum(1)), axis=1)


def primes_below(limit):
    # Odd-only sieve, independent of the source's full boolean sieve.
    sieve = bytearray(b'\x01') * ((limit + 1) // 2)
    sieve[0] = 0
    for candidate in range(3, int(limit ** .5) + 1, 2):
        if sieve[candidate // 2]:
            start = candidate * candidate // 2
            sieve[start::candidate] = b'\x00' * len(sieve[start::candidate])
    return [2] + [2 * i + 1 for i, flag in enumerate(sieve) if flag and 2 * i + 1 < limit]


def produce():
    plan = json.loads((HERE / 'plan.json').read_text())
    amended = json.loads((HERE / 'amendment.json').read_text())
    assert hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest() == amended['original_plan_sha256']
    raw = grid_bytes()
    observed = measures(np.frombuffer(raw, dtype=np.uint8)[None, :])[0]
    rng = np.random.default_rng(amended['seed'])
    null = np.concatenate([measures(rng.integers(0, 256, (10000, 256), dtype=np.uint8)) for _ in range(10)])
    measurements = []
    for index, name in enumerate(NAMES):
        value, sample = float(observed[index]), null[:, index]
        below = int(np.count_nonzero(sample <= value))
        above = int(np.count_nonzero(sample >= value))
        p = min(1., 2 * min((below + 1) / 100001, (above + 1) / 100001))
        measurements.append(dict(name=name, observed=value, null_mean=float(sample.mean()),
                                 null_at_or_below=below, null_at_or_above=above,
                                 two_sided_tail=p, threshold=.01 / 7,
                                 rejected_uniform_reference=p < .01 / 7))
    column = bytes(raw[r * 8 + c] for c in range(8) for r in range(32))
    primes = primes_below(plan['rules']['factor_bound_exclusive'])
    integers = []
    for name, sequence in (('R', raw), ('C', column)):
        for order in ('big', 'little'):
            number = int.from_bytes(sequence, order)
            factors = [q for q in primes if number % q == 0]
            failures = []
            if number % 2 == 0: failures.append('even')
            if number.bit_length() != 2048: failures.append('not 2048 bits')
            if factors: failures.append('small prime divisor')
            integers.append(dict(route=name, order=order, integer_decimal=str(number),
                                 bit_length=number.bit_length(), small_prime_divisors=factors,
                                 fails_conventional_modulus_screen=bool(failures), failures=failures))
    return dict(schema='liberpedia-grid-byte-structure-v1',
                plan_sha256=hashlib.sha256((HERE / 'plan.json').read_bytes()).hexdigest(),
                amendment_sha256=hashlib.sha256((HERE / 'amendment.json').read_bytes()).hexdigest(),
                grid_sha256=hashlib.sha256(raw).hexdigest(), null_draws=100000,
                measurements=measurements, primes_checked=len(primes), integers=integers)


if __name__ == '__main__':
    result = produce()
    path = HERE / 'results.json'
    if sys.argv[1:] == ['--check']:
        assert result == json.loads(path.read_text())
        print('PASS: seven 100,000-draw reference checks and four complete small-prime screens')
    elif not sys.argv[1:]:
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8', newline='\n')
        print(json.dumps({'statistics': result['measurements'], 'integers': [
            {k: v for k, v in row.items() if k != 'integer_decimal'} for row in result['integers']]}))
    else:
        raise SystemExit('Usage: run.py [--check]')
