"""Independent identities for the fixed two-plaintext-rune sum decoder.

This checks algebra and implementation, not manuscript plaintext or language.
Run from any directory. No target text is loaded.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'source/analysis/round12/C1/feedback.py'


def recurrence(cipher, primer):
    plain = []
    for i, value in enumerate(cipher):
        key = primer[i] if i < 2 else plain[i - 1] + plain[i - 2]
        plain.append((value - key) % 29)
    return plain


def difference_decode(cipher, primer):
    plain = recurrence(cipher[:3], primer)
    for i in range(3, len(cipher)):
        plain.append((cipher[i] - cipher[i - 1] + plain[i - 3]) % 29)
    return plain


def encrypt(plain, primer):
    return [(value + (primer[i] if i < 2 else plain[i - 1] + plain[i - 2])) % 29
            for i, value in enumerate(plain)]


def main():
    spec = importlib.util.spec_from_file_location('source_feedback', SOURCE)
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    rng = random.Random(241026)
    lengths = [0, 1, 2, 3, 4, 29, 57, 200]
    count = positions = 0
    digest = hashlib.sha256()
    for length in lengths:
        cipher = [rng.randrange(29) for _ in range(length)]
        baseline = recurrence(cipher, (0, 0))
        for first in range(29):
            for second in range(29):
                primer = (first, second)
                plain = recurrence(cipher, primer)
                assert plain == difference_decode(cipher, primer)
                assert plain == source.decode(cipher, source.f_sum, 2, primer, source='pt', sign=-1)
                shifts = (-first, -second, first + second)
                assert plain == [(p + shifts[i % 3]) % 29 for i, p in enumerate(baseline)]
                assert encrypt(plain, primer) == cipher
                digest.update(bytes(plain))
                count += 1
                positions += length
    result = {
        'status': 'pass', 'target_data_loaded': False, 'random_seed': 241026,
        'lengths': lengths, 'primer_pairs_per_stream': 841,
        'cases': count, 'rune_positions_checked': positions,
        'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'checked_plaintexts_sha256': digest.hexdigest(),
        'identities': [
            'P[i] = C[i] - P[i-1] - P[i-2] mod29 for i>=2',
            'P[i] = C[i] - C[i-1] + P[i-3] mod29 for i>=3',
            'relative to zero primer, changes repeat (-s0,-s1,s0+s1) every three positions'
        ],
        'limits': 'Only fixed k2 plaintext-sum feedback with sign minus and initial additive key values. Does not apply to nonlinear, mixed-history or skip-aware variants. No evidence of an LP2 solution.'
    }
    output = HERE / 'independent/algebra-check.json'
    assert json.loads(output.read_bytes()) == result, 'Independent algebra receipt differs.'
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
