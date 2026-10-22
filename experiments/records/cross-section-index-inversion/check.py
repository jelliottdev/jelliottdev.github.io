"""Independent source, quotient and line-index audit of the 729/index proposal."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan_bytes = (HERE / 'plan.json').read_bytes()
plan = json.loads(plan_bytes)
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
assert saved['plan_sha256'] == hashlib.sha256(plan_bytes).hexdigest()

alphabet = plan['runes']
assert len(alphabet) == 29 and len(set(alphabet)) == 29
primes = []
candidate = 2
while len(primes) < 29:
    if all(candidate % factor for factor in range(2, int(candidate**0.5) + 1)):
        primes.append(candidate)
    candidate += 1
assert primes == plan['prime_values']

source = []
for number, dependency in enumerate(plan['inputs']):
    path = ROOT / dependency['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == dependency['sha256']
    local_line = 0
    for line in path.read_text(encoding='utf-8').splitlines():
        if not any(c in alphabet for c in line):
            continue
        local_line += 1
        for char in line:
            if char in alphabet:
                source.append((f'lp2-{number:02d}', local_line, char))
assert len(source) == len(saved['trace']) == 729
assert [x['rune_count'] for x in saved['page_counts']] == [262, 266, 201]
assert [x['rune_rows'] for x in saved['page_counts']] == [12, 12, 9]
assert saved['total_rune_rows'] == 33

zero = global_out = local_out = convention_differences = 0
last_page = None
global_line = 0
last_local_line = 0
for number, ((page, local_line, char), row) in enumerate(zip(source, saved['trace']), 1):
    if (page, local_line) != (last_page, last_local_line):
        global_line += 1
        last_page, last_local_line = page, local_line
    idx = alphabet.index(char)
    assert (row['position'], row['page'], row['page_line'], row['global_line'], row['rune'], row['index'], row['prime_value']) == (number, page, local_line, global_line, char, idx, primes[idx])
    if idx == 0:
        zero += 1
        assert row['undefined'] == '729/0'
        assert 'base_index' not in row
        continue
    ratio = Fraction(729, idx)
    floor = ratio.numerator // ratio.denominator
    remainder = 729 - floor * idx
    fractional = ratio - floor
    direction = 1 if fractional > Fraction(1, 2) else -1 if fractional < Fraction(1, 2) else 0
    base = floor % 29
    assert (row['quotient_floor'], row['remainder'], row['direction'], row['base_index']) == (floor, remainder, direction, base)
    assert row['base_label'] == plan['latin_labels'][base]
    for key, line_number in [('global', global_line), ('page', local_line)]:
        raw = base + direction * line_number
        assert row[key + '_raw_index'] == raw
        assert row[key + '_wrapped_index'] == raw % 29
        assert row[key + '_wrapped_label'] == plan['latin_labels'][raw % 29]
    global_out += not 0 <= row['global_raw_index'] < 29
    local_out += not 0 <= row['page_raw_index'] < 29
    convention_differences += row['global_wrapped_index'] != row['page_wrapped_index']

assert (zero, global_out, local_out, convention_differences) == (
    saved['zero_index_count'], saved['global_out_of_range_without_wrap'],
    saved['page_out_of_range_without_wrap'], saved['page_vs_global_wrapped_differences'])
assert zero == 34
first = saved['trace'][:8]
assert [r['index'] for r in first] == [15, 8, 18, 3, 6, 19, 27, 0]
assert plan['source_first_word_claimed_indices'] == [15, 8, 18, 3, 6, 19, 28, 0]
assert [r.get('global_wrapped_label', '*') for r in first] == ['L', 'O', 'J', 'I', 'C/K', 'H', 'Y', '*']
assert saved['source_index_mismatch_positions'] == [7]
print('PASS: 729 source positions, 34 undefined divisions, first-word index mismatch and both line conventions')
