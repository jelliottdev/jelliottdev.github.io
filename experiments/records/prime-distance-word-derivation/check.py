"""Independent token, arithmetic and edit-distance checks for the source replay."""
import hashlib
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan_bytes = (HERE / 'plan.json').read_bytes()
plan = json.loads(plan_bytes)
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert saved['plan_sha256'] == hashlib.sha256(plan_bytes).hexdigest()
for dependency in plan['inputs']:
    assert hashlib.sha256((ROOT / dependency['path']).read_bytes()).hexdigest() == dependency['sha256']

p15 = (ROOT / 'text/lp2-15.txt').read_text(encoding='utf-8')
p16 = (ROOT / 'text/lp2-16.txt').read_text(encoding='utf-8')
heading = p15[:p15.index('&')]
body = p15[p15.index('$') + 1:] + p16[:p16.index(plan['next_section_marker'])]
alphabet = set(plan['runes'])


def split_words(raw):
    # Scan rune runs independently of the producer's regular-expression split.
    raw = raw.replace('/\n', '')
    out, current = [], []
    for char in raw:
        if char in alphabet:
            current.append(char)
        elif current:
            out.append(''.join(current))
            current = []
    if current:
        out.append(''.join(current))
    return out


words = split_words(heading) + split_words(body)
assert len(split_words(heading)) == 2
assert len(words) == saved['word_count'] == 57
values = dict(zip(plan['runes'], plan['prime_values']))


def prime(n):
    return n >= 2 and all(n % divisor for divisor in range(2, int(n**0.5) + 1))


digits = []
for number, (word, trace) in enumerate(zip(words, saved['tokens']), 1):
    total = sum(values[c] for c in word)
    assert trace['number'] == number and trace['runes'] == word and trace['prime_sum'] == total
    delta = 0
    while not (prime(total - delta) or prime(total + delta)):
        delta += 1
    assert trace['nearest_prime_distance'] == delta
    digits.append(str(delta))
archived = ''.join(digits)
reported = plan['reported_digits']
assert archived == saved['archived_digits']
assert reported == saved['reported_digits'] and len(reported) == 53

# The report and archive differ by four word positions plus at least three
# digit substitutions. Dynamic-programming distance does not assume the
# producer's SequenceMatcher alignment is uniquely attributable to words.
prev = list(range(len(reported) + 1))
for i, a in enumerate(archived, 1):
    row = [i]
    for j, b in enumerate(reported, 1):
        row.append(min(prev[j] + 1, row[-1] + 1, prev[j - 1] + (a != b)))
    prev = row
assert prev[-1] == 7
assert len(saved['alignment']) == 57
assert ''.join(str(x['archived_digit']) for x in saved['alignment'] if x['archived_digit'] is not None) == archived
assert ''.join(str(x['reported_digit']) for x in saved['alignment'] if x['reported_digit'] is not None) == reported

column_sums = [int(a) + int(b) for a, b in zip(archived, archived[::-1])]
assert max(column_sums) == 8 and all(x < 10 for x in column_sums)
assert column_sums[0] > 0
assert ''.join(map(str, column_sums)) == saved['archive_reverse_add']
assert saved['archive_sum_is_palindrome']

control = saved['shuffle_control']
assert control['trials'] == plan['shuffle_trials'] == 100000
assert control['seed'] == plan['shuffle_seed']
rng = random.Random(control['seed'])
shuffled = list(archived)
hits = 0
for _ in range(control['trials']):
    rng.shuffle(shuffled)
    paired = [int(a) + int(b) for a, b in zip(shuffled, reversed(shuffled))]
    hits += max(paired) < 10 and paired[0] > 0
assert hits == control['palindromes']
print('PASS: 57 source words and prime distances, minimum edit distance 7, no-carry sum and 100,000 controls')
