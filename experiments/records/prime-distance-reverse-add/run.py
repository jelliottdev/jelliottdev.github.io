"""Replay a reported reverse-add palindrome and a fixed digit-multiset control."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assess(s):
    paired = [int(a) + int(b) for a, b in zip(s, reversed(s))]
    total = str(int(s) + int(s[::-1]))
    return paired, total, total == total[::-1], max(paired) < 10 and paired[0] > 0


def make_results():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    s = plan['reported_decimal_string']
    assert len(s) == 53 and s.isdecimal() and s[0] == '0'
    assert plan['source_sha256'] == '8972147d268ee1910444a63caf71421ceac5c727fd3a36b6dfdd81454c6baf7c'
    paired, total, palindrome, no_carry = assess(s)
    assert s[::-1] == plan['reported_reverse']
    assert total == plan['reported_sum']
    rng = random.Random(plan['seed'])
    digits = list(s)
    control_palindromes = control_no_carry = 0
    for _ in range(plan['trials']):
        rng.shuffle(digits)
        _, _, is_palindrome, is_no_carry = assess(''.join(digits))
        control_palindromes += is_palindrome
        control_no_carry += is_no_carry
    return {
        'plan_sha256': digest(plan_path),
        'input_length': len(s),
        'digit_counts': dict(sorted(Counter(s).items())),
        'reported_string': s,
        'reported_reverse': s[::-1],
        'reported_sum': total,
        'sum_is_palindrome': palindrome,
        'paired_sums': paired,
        'maximum_paired_sum': max(paired),
        'no_carry_with_nonzero_outer_pair': no_carry,
        'control': {
            'model': 'Uniform random shuffles of the reported 53-character digit multiset, with leading zero allowed in the string',
            'seed': plan['seed'], 'trials': plan['trials'],
            'palindromes': control_palindromes,
            'no_carry_with_nonzero_outer_pair': control_no_carry,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare fresh results with saved JSON')
    args = parser.parse_args()
    fresh = make_results()
    saved = HERE / 'results.json'
    if args.check:
        assert fresh == json.loads(saved.read_text(encoding='utf-8'))
        print('PASS: reverse-add arithmetic and fixed-multiset controls match saved results')
    else:
        print(json.dumps(fresh, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
