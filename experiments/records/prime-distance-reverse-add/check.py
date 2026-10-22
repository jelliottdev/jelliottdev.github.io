"""Independently verify the fixed reverse-add arithmetic and carry explanation."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
saved = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
s = plan['reported_decimal_string']
assert len(s) == 53 and all('0' <= c <= '9' for c in s)
assert ''.join(reversed(s)) == plan['reported_reverse'] == saved['reported_reverse']
assert sum(saved['digit_counts'].values()) == 53
assert {str(i): s.count(str(i)) for i in range(10) if str(i) in s} == saved['digit_counts']

# Column arithmetic is checked separately from run.py's full-integer addition.
columns = [int(s[i]) + int(s[-1-i]) for i in range(len(s))]
assert columns == saved['paired_sums']
assert columns == columns[::-1]
assert all(column < 10 for column in columns)
assert columns[0] > 0
constructed = ''.join(map(str, columns))
assert constructed == plan['reported_sum'] == saved['reported_sum']
assert constructed == constructed[::-1]

control = saved['control']
assert control['trials'] == plan['trials'] == 100000
assert control['seed'] == plan['seed'] == 3301
assert 0 <= control['palindromes'] <= control['trials']
assert control['palindromes'] == control['no_carry_with_nonzero_outer_pair']
print('PASS: reported 53-digit sum is column-wise symmetric with no carries; saved control counts are internally consistent')
