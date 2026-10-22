"""Derive every first-section nearest-prime word distance from archived LP2-15/16."""
import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import random
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def primes_through(bound):
    out = []
    for n in range(2, bound + 1):
        if all(n % p for p in out if p * p <= n):
            out.append(n)
    return out


def source_words(plan):
    for item in plan['inputs']:
        assert digest(ROOT / item['path']) == item['sha256']
    p15 = (ROOT / 'text/lp2-15.txt').read_text(encoding='utf-8')
    p16 = (ROOT / 'text/lp2-16.txt').read_text(encoding='utf-8')
    assert p15.count('&') == p15.count('$') == 1
    assert p16.count(plan['next_section_marker']) == 1
    heading = p15.split('&', 1)[0]
    body = p15.split('$', 1)[1] + p16.split(plan['next_section_marker'], 1)[0]
    heading_words = re.findall('[' + plan['runes'] + ']+', heading.replace('/\n', ''))
    body_words = re.findall('[' + plan['runes'] + ']+', body.replace('/\n', ''))
    assert len(heading_words) == 2
    return heading_words + body_words


def alignment(observed, reported):
    rows = []
    for tag, i, j, k, m in SequenceMatcher(None, observed, reported, autojunk=False).get_opcodes():
        width = max(j - i, m - k)
        for pos in range(width):
            ai = i + pos if pos < j - i else None
            ri = k + pos if pos < m - k else None
            rows.append({'archived_word': None if ai is None else ai + 1,
                         'archived_digit': None if ai is None else int(observed[ai]),
                         'reported_position': None if ri is None else ri + 1,
                         'reported_digit': None if ri is None else int(reported[ri]),
                         'same': ai is not None and ri is not None and observed[ai] == reported[ri]})
    return rows


def make_results():
    plan_path = HERE / 'plan.json'
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    assert len(plan['runes']) == len(plan['prime_values']) == 29
    assert primes_through(109) == plan['prime_values']
    words = source_words(plan)
    values = dict(zip(plan['runes'], plan['prime_values']))
    sums = [sum(values[c] for c in word) for word in words]
    nearby = primes_through(max(sums) + 100)
    distances = [min(abs(total - prime) for prime in nearby) for total in sums]
    assert all(0 <= n <= 9 for n in distances)
    observed = ''.join(map(str, distances))
    reported = plan['reported_digits']
    total = str(int(observed) + int(observed[::-1]))
    assert len(reported) == 53 and len(observed) == 57
    assert total == total[::-1]
    rng = random.Random(plan['shuffle_seed'])
    digits = list(observed)
    control_hits = 0
    for _ in range(plan['shuffle_trials']):
        rng.shuffle(digits)
        sampled = ''.join(digits)
        added = str(int(sampled) + int(sampled[::-1]))
        control_hits += added == added[::-1]
    return {
        'plan_sha256': digest(plan_path),
        'word_count': len(words),
        'tokens': [{'number': i + 1, 'runes': word, 'prime_sum': s, 'nearest_prime_distance': d}
                   for i, (word, s, d) in enumerate(zip(words, sums, distances))],
        'archived_digits': observed,
        'reported_digits': reported,
        'alignment': alignment(observed, reported),
        'archive_reverse_add': total,
        'archive_sum_is_palindrome': total == total[::-1],
        'archive_digit_counts': dict(sorted(Counter(observed).items())),
        'shuffle_control': {'seed': plan['shuffle_seed'], 'trials': plan['shuffle_trials'],
                            'palindromes': control_hits, 'model': 'Shuffle the complete 57-digit archived distance multiset; retain the leading-zero convention.'}
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    fresh = make_results()
    path = HERE / 'results.json'
    if args.write:
        path.write_text(json.dumps(fresh, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
        print('Wrote', path)
    elif args.check:
        assert fresh == json.loads(path.read_text(encoding='utf-8'))
        print('PASS: 57 word distances, source comparison, palindrome and 100,000 shuffles')
    else:
        print(json.dumps(fresh, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
