"""Portable fixed-slot baseline; original pre-target freeze is in source-freeze.json."""
import argparse
import hashlib
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LABELS = {
    'IA_one': ['E', 'G', 'A', 'L', 'I', 'T', 'A', 'R', 'IA', 'N', 'I', 'S', 'M'],
    'IA_separate': list('EGALITARIANISM'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + '\n'
    if CHECK:
        assert (HERE/name).read_text(encoding='utf8') == encoded, name
    else:
        (HERE/name).write_text(encoded, encoding='utf8')


def encodings():
    alphabet = json.loads((HERE / 'alphabet.json').read_text(encoding='utf8'))
    lookup = {row['latin']: row['index'] for row in alphabet}
    return {name: [lookup[label] for label in labels] for name, labels in LABELS.items()}


def static(cipher, plain, modulus):
    if len(cipher) != len(plain):
        return {'eligible': False, 'reason': 'whole-slot length mismatch', 'cipher_length': len(cipher), 'plain_length': len(plain)}
    forward, reverse, conflicts = {}, {}, []
    for i, (c, p) in enumerate(zip(cipher, plain)):
        if c in forward and forward[c] != p:
            conflicts.append({'position': i, 'kind': 'one ciphertext symbol to two plaintext symbols', 'cipher': c, 'prior_plain': forward[c], 'plain': p})
        if p in reverse and reverse[p] != c:
            conflicts.append({'position': i, 'kind': 'two ciphertext symbols to one plaintext symbol', 'plain': p, 'prior_cipher': reverse[p], 'cipher': c})
        forward.setdefault(c, p)
        reverse.setdefault(p, c)
    return {'eligible': True, 'compatible': not conflicts, 'assignments': [[c, p] for c, p in sorted(forward.items())],
            'distinct_cipher_symbols': len(forward), 'extensions': math.factorial(modulus-len(forward)) if not conflicts else 0, 'conflicts': conflicts}


def affine(cipher, plain, modulus):
    if len(cipher) != len(plain):
        return []
    return [{'a': a, 'b': b, 'fits': not (bad := [i for i, (c, p) in enumerate(zip(cipher, plain)) if (a*c+b) % modulus != p]),
             'conflict_positions': bad}
            for a in range(1, modulus) if math.gcd(a, modulus) == 1 for b in range(modulus)]


def controls():
    # No page text, prepared slot, or image is opened in this phase.
    cohorts, all_keys = [], []
    for name, plain in encodings().items():
        context = [(7*i+3) % 29 for i in range(274)]
        context[37:37+len(plain)] = plain
        for variant in ['affine', 'swapped-output-0-1']:
            permutation = [(5*p+11) % 29 for p in range(29)]
            if variant != 'affine':
                permutation = [1 if c == 0 else 0 if c == 1 else c for c in permutation]
            assert len(set(permutation)) == 29
            inverse = {c: p for p, c in enumerate(permutation)}
            ciphertext = [permutation[p] for p in context]
            assert [inverse[c] for c in ciphertext] == context
            assert [inverse[permutation[p]] for p in range(29)] == list(range(29))
            observed = static(ciphertext[37:37+len(plain)], plain, 29)
            assert observed['compatible']
            assert all(inverse[c] == p for c, p in observed['assignments'])
            cohorts.append({'encoding': name, 'variant': variant, 'plaintext': context, 'ciphertext': ciphertext,
                            'permutation': permutation, 'slot_length': len(plain), 'static': observed,
                            'affine_fits': [[row['a'], row['b']] for row in affine(ciphertext[37:37+len(plain)], plain, 29) if row['fits']]})
        for a in range(1, 29):
            for b in range(29):
                ciphertext = [(a*p+b) % 29 for p in context]
                decoder = (pow(a, -1, 29), (-pow(a, -1, 29)*b) % 29)
                fits = [(row['a'], row['b']) for row in affine(ciphertext[37:37+len(plain)], plain, 29) if row['fits']]
                assert decoder in fits
                assert [(decoder[0]*c+decoder[1]) % 29 for c in ciphertext] == context
                all_keys.append({'encoding': name, 'encoder': [a, b], 'planted_decoder': list(decoder), 'returned': fits})
    failures = [static([1, 1], [2, 3], 29), static([1, 2], [3, 3], 29), static([0]*14, [0]*13, 29)]
    assert not failures[0]['compatible'] and not failures[1]['compatible'] and not failures[2]['eligible']
    exhaustive = []
    for modulus in [2, 3]:
        for length in range(5):
            words = list(itertools.product(range(modulus), repeat=length))
            for cipher in words:
                for plain in words:
                    result = static(cipher, plain, modulus)
                    exhaustive.append({'modulus': modulus, 'cipher': cipher, 'plain': plain, 'extensions': result['extensions'],
                                       'affine_fits': [[row['a'], row['b']] for row in affine(cipher, plain, modulus) if row['fits']]})
    assert len(exhaustive) == 7722
    write('controls.json', {'schema': 'egalitarianism-baseline-controls-v1', 'target_evaluated': False,
                           'planted_contexts': cohorts, 'all_affine_plants': all_keys, 'deliberate_failures': failures, 'small_alphabets': exhaustive})
    print('Controls passed: 4 contexts, 1624 planted affine keys, 3 deliberate failures, 7722 exhaustive pairs.')


def target():
    plan = json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    for item in plan['files']:
        assert digest(HERE/item['name']) == item['sha256'], item['name']
    inputs = json.loads((HERE/'inputs.json').read_text(encoding='utf8'))
    alphabet = json.loads((HERE/'alphabet.json').read_text(encoding='utf8'))
    lookup = {row['rune']: row['index'] for row in alphabet}
    raw = (HERE/'page.txt').read_bytes().decode('utf8')
    positions = []
    offset = 0
    for line_number, line in enumerate(raw.splitlines(keepends=True), 1):
        in_line = 0
        for column, char in enumerate(line):
            if char in lookup:
                positions.append({'page_rune_zero_based': len(positions), 'physical_line_one_based': line_number,
                                  'line_rune_zero_based': in_line, 'raw_character_zero_based': offset+column,
                                  'rune': char, 'index': lookup[char]})
                in_line += 1
        offset += len(line)
    slot = inputs['slot']
    assert (slot['start_zero_based'], slot['end_exclusive'], slot['length']) == (37, 51, 14)
    assert len(positions) == inputs['page_rune_count'] == 274
    assert positions[37:51] == slot['positions']
    assert raw[positions[37]['raw_character_zero_based']-1] == raw[positions[50]['raw_character_zero_based']+1] == '-'
    assert ''.join(c for c in raw[positions[37]['raw_character_zero_based']:positions[50]['raw_character_zero_based']+1] if c not in lookup) == '/\n'
    cipher = [row['index'] for row in positions[37:51]]
    cases = []
    for name, plain in encodings().items():
        assert inputs['encodings'][name]['indices'] == plain
        mapping = static(cipher, plain, 29)
        ledger = affine(cipher, plain, 29) if mapping['eligible'] else []
        cases.append({'encoding': name, 'labels': LABELS[name], 'indices': plain, 'static': mapping,
                      'affine_decoders': ledger, 'affine_fit_count': sum(row['fits'] for row in ledger)})
    # No continuation is part of this saved all-incompatible result.
    assert not any(case['static'].get('compatible') or case['affine_fit_count'] for case in cases)
    write('target-results.json', {'schema': 'egalitarianism-fixed-slot-public-baseline-v1',
                                'new_baseline_not_historical_replay': True, 'plan_sha256': digest(HERE/'plan.json'),
                                'source_freeze_sha256': digest(HERE/'source-freeze.json'),
                                'page': 'lp2-43', 'slot': [37, 51], 'cipher_indices': cipher, 'cases': cases})
    print('Fixed target: 13-rune encoding length-ineligible; 14-rune encoding incompatible; zero of 812 affine decoders fit.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    CHECK = parser.parse_args().check
    controls()
    target()


