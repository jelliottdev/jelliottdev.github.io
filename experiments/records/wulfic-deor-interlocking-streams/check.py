"""Independent input, source-witness, and full-control checks for the Deor replay."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re

from run import HERE, ROOT, execute, inputs, split


def pair_ioc(values):
    buckets = defaultdict(int)
    for value in values:
        buckets[value] += 1
    n = len(values)
    return sum(count * (count - 1) for count in buckets.values()) / (n * (n - 1))


def main():
    saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    vals, poem, hashes = inputs()
    assert len(vals) == 217 and len(poem) == 960
    assert hashes == saved['input_sha256']
    prime, other = split(vals)
    assert len(prime) == 65 and len(other) == 152
    assert all(value in {2, 3, 5, 7, 11, 13, 17, 19, 23} for value in prime)
    assert all(value not in {2, 3, 5, 7, 11, 13, 17, 19, 23} for value in other)

    # Reconstruct the selected outputs without calling the production decoders.
    observed = saved['observed']
    first = [(prime[i] + poem[47 + i]) % 29 for i in range(65)]
    assert hashlib.sha256(bytes(first)).hexdigest() == observed['first']['decoded_sha256']
    assert abs(pair_ioc(first) - observed['first']['raw_ioc']) < 1e-15
    key = [first[(31 + i) % 65] for i in range(152)]
    second = [(other[i] - key[i]) % 29 for i in range(152)]
    assert hashlib.sha256(bytes(second)).hexdigest() == observed['second']['decoded_sha256']
    assert abs(pair_ioc(second) - observed['second']['raw_ioc']) < 1e-15
    assert observed['first_candidate_count'] == 1800
    assert observed['second_candidate_count'] == 195
    assert observed['original_second_hits'] == 0
    assert observed['amended_second_screen_hits'] == 0

    trace = (HERE / 'source-run.txt').read_text(encoding='utf-8')
    assert 'Deor stream: 960 values' in trace
    assert 'Best prime-stream: mode=add off=47 IoC=0.0649' in trace
    assert 'Best IoC non-prime from prime_pl: 0.0404' in trace
    assert not re.search(r'\bHIT:', trace)
    assert 0 <= pair_ioc(first) <= 1 and 0 <= pair_ioc(second) <= 1
    for shift in range(29):
        assert abs(pair_ioc([(value - shift) % 29 for value in other]) - saved['observed']['caesar_raw_ioc']) < 1e-15
    assert saved['null_trials'] == len(saved['null']) == 199
    assert saved['null_second_ge_observed'] == sum(
        row['second_normalized_ioc'] >= observed['second']['normalized_ioc'] for row in saved['null']) == 110
    assert saved['null_first_ge_observed'] == sum(
        row['first_normalized_ioc'] >= observed['first']['normalized_ioc'] for row in saved['null']) == 18
    assert execute() == saved
    print('PASS: pinned inputs, source stdout, scalar selected decodes, impossible gates, and 199 full nulls')


if __name__ == '__main__':
    main()
