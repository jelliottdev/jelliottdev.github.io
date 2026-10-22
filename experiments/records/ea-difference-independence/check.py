"""Independent source parser and exact observed-statistic check."""
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def main():
    result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE / 'plan.txt').read_bytes()).hexdigest() == result['plan_sha256']
    index_raw = (ROOT / 'data/index.json').read_bytes()
    assert hashlib.sha256(index_raw).hexdigest() == result['input_sha256']['data/index.json']
    alphabet = json.loads(index_raw)['alphabet']
    lookup = {entry['rune']: i for i, entry in enumerate(alphabet)}
    assert len(lookup) == 29
    counts = Counter()
    transitions = zeros = eligible = equal = 0
    for page_number in range(56):
        name = f'text/lp2-{page_number:02d}.txt'
        raw = (ROOT / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == result['input_sha256'][name]
        # Extract the entire Runic Unicode block, then refuse any glyph outside the alphabet.
        symbols = re.findall('[\u16a0-\u16ff]', raw.decode('utf-8'))
        assert all(symbol in lookup for symbol in symbols), name
        numbers = [lookup[symbol] for symbol in symbols]
        page_deltas = [((right - left) % 29) for left, right in zip(numbers, numbers[1:])]
        transitions += len(page_deltas)
        zeros += page_deltas.count(0)
        counts.update(delta for delta in page_deltas if delta != 0)
        for left, right in zip(page_deltas, page_deltas[1:]):
            if left != 0 and right != 0:
                eligible += 1
                equal += (left == right)
    observed = result['observed']
    n = sum(counts.values())
    histogram = [counts[i] for i in range(1, 29)]
    exact_chi = Fraction(28 * sum(c*c for c in histogram), n) - n
    assert transitions == result['within_page_transitions'] == 12901
    assert zeros == result['zero_differences'] == 86
    assert n == observed['nonzero_count'] == 12815
    assert histogram == observed['nonzero_histogram']
    assert abs(float(exact_chi) - observed['chi_square']) < 1e-10
    assert eligible == observed['adjacent_nonzero_pairs'] == 12676
    assert equal == observed['adjacent_equal_nonzero'] == 432
    assert Fraction(eligible, 28) == Fraction.from_float(observed['adjacent_equal_expected']).limit_denominator(28)
    assert result['reference']['synthetic_cipher_round_trip'] is True
    for metric in ('chi_square', 'adjacent_equal_nonzero'):
        item = result['reference'][metric]
        assert len(item['central_95']) == 2 and item['central_95'][0] <= item['central_95'][1]
        assert 0 <= item['at_least_observed'] <= result['reference']['trials']
        assert 0 <= item['at_most_observed'] <= result['reference']['trials']
    print('PASS: independent Runic-block extraction, source hashes, 28 bins and adjacent-difference statistic')


if __name__ == '__main__':
    main()
