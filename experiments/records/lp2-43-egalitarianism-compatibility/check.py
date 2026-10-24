"""Independent equality-pair/permutation and derived-key checks; no producer imports."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def expected_extensions(cipher, plain, size):
    if len(cipher) != len(plain):
        return None
    equality = all((cipher[i] == cipher[j]) == (plain[i] == plain[j]) for i in range(len(cipher)) for j in range(i))
    return math.factorial(size-len(set(cipher))) if equality else 0


def derived_keys(cipher, plain, size):
    if len(cipher) != len(plain):
        return []
    pair = next(((i, j) for i in range(len(cipher)) for j in range(i) if cipher[i] != cipher[j]), None)
    if pair:
        i, j = pair
        a = ((plain[i]-plain[j])*pow((cipher[i]-cipher[j]) % size, -1, size)) % size
        candidates = [(a, (plain[j]-a*cipher[j]) % size)] if a and math.gcd(a, size) == 1 else []
    elif cipher:
        candidates = [(a, (plain[0]-a*cipher[0]) % size) for a in range(1, size) if math.gcd(a, size) == 1]
    else:
        candidates = [(a, b) for a in range(1, size) if math.gcd(a, size) == 1 for b in range(size)]
    return sorted([list(key) for key in candidates if all((key[0]*c+key[1]) % size == p for c, p in zip(cipher, plain))])


def controls():
    raw = (HERE/'controls.json').read_bytes()
    data = json.loads(raw)
    for row in data['small_alphabets']:
        c, p, size = row['cipher'], row['plain'], row['modulus']
        enumerated = sum(all(permutation[x] == y for x, y in zip(c, p)) for permutation in itertools.permutations(range(size)))
        assert row['extensions'] == enumerated == expected_extensions(c, p, size)
        assert sorted(row['affine_fits']) == derived_keys(c, p, size)
    assert len(data['small_alphabets']) == 7722
    for row in data['planted_contexts']:
        c, p = row['ciphertext'], row['plaintext']
        assert len(c) == len(p) == 274
        assert all(c[i] == row['permutation'][p[i]] for i in range(274))
        assert len(set(row['permutation'])) == 29
        n = row['slot_length']
        assert row['static']['extensions'] == expected_extensions(c[37:37+n], p[37:37+n], 29)
        assert sorted(row['affine_fits']) == derived_keys(c[37:37+n], p[37:37+n], 29)
        assert all(row['permutation'][plain] == cipher for cipher, plain in row['static']['assignments'])
    for row in data['all_affine_plants']:
        a, b = row['encoder']; da, db = row['planted_decoder']
        assert all((da*((a*p+b) % 29)+db) % 29 == p for p in range(29))
        assert row['planted_decoder'] in row['returned']
        context = next(r for r in data['planted_contexts'] if r['encoding'] == row['encoding'])
        plaintext = context['plaintext'][37:37+context['slot_length']]
        ciphertext = [(a*p+b) % 29 for p in plaintext]
        assert sorted(row['returned']) == derived_keys(ciphertext, plaintext, 29)
    assert len(data['all_affine_plants']) == 1624
    assert expected_extensions([1, 1], [2, 3], 29) == expected_extensions([1, 2], [3, 3], 29) == 0
    assert expected_extensions([0]*14, [0]*13, 29) is None
    result = {'passed': True, 'target_evaluated': False, 'controls_sha256': hashlib.sha256(raw).hexdigest(),
              'small_alphabet_pairs': 7722, 'planted_contexts': 4, 'all_affine_plants': 1624, 'deliberate_failures': 3}
    assert json.loads((HERE/'controls-check.json').read_text(encoding='utf8')) == result, 'Independent control receipt mismatch'
    print('Independent controls passed: exhaustive permutation counts and derived affine keys agree in all 7722 pairs.')


def target():
    raw = (HERE/'target-results.json').read_bytes(); data = json.loads(raw)
    cipher = data['cipher_indices']
    for case in data['cases']:
        plain = case['indices']; expected = expected_extensions(cipher, plain, 29)
        assert case['static']['eligible'] == (expected is not None)
        if expected is None:
            assert not case['affine_decoders']
            continue
        assert case['static']['extensions'] == expected
        assert len(case['affine_decoders']) == 812
        assert {(r['a'], r['b']) for r in case['affine_decoders']} == set(itertools.product(range(1, 29), range(29)))
        for row in case['affine_decoders']:
            bad = [i for i in range(len(cipher)) if (row['a']*cipher[i]+row['b']) % 29 != plain[i]]
            assert row['conflict_positions'] == bad and row['fits'] == (not bad)
        fits = [[r['a'], r['b']] for r in case['affine_decoders'] if r['fits']]
        assert sorted(fits) == derived_keys(cipher, plain, 29)
        assert case['affine_fit_count'] == len(fits)
    result = {'passed': True, 'target_sha256': hashlib.sha256(raw).hexdigest(), 'cases': len(data['cases']),
              'checks': ['whole-slot length', 'pairwise equality relation', 'complete affine ledger', 'algebraically derived affine candidates']}
    assert json.loads((HERE/'target-check.json').read_text(encoding='utf8')) == result, 'Independent target receipt mismatch'
    print('Independent target check passed: length/equality relation and all 812 affine outcomes agree.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=['controls', 'target'])
    {'controls': controls, 'target': target}[parser.parse_args().phase]()
