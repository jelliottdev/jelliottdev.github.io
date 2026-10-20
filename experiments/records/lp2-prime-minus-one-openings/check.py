"""Independent trial-division and inverse-arithmetic audit of saved candidates."""
import csv
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
result = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert result['plan_sha256'] == sha(HERE/'plan.json')
for item in plan['inputs']:
    assert sha(ROOT/item['path']) == item['sha256'], item['path']
alphabet = [r['rune'] for r in json.loads(
    (ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']]
streams = {p: [alphabet.index(c) for c in (ROOT/'text'/(p+'.txt')).read_text(
    encoding='utf-8') if c in alphabet] for p in plan['pages']}
keys = []
n = 2
while len(keys) < max(map(len, streams.values())) + max(plan['offsets']):
    if all(n % d for d in range(2, math.isqrt(n)+1)):
        keys.append(n-1)
    n += 1
assert result['shifts'] == keys
assert keys[:6] == [1, 2, 4, 6, 10, 12]
assert result['page_lengths'] == {p: len(s) for p, s in streams.items()}
assert result['empty_pages'] == [p for p, s in streams.items() if not s]
for opening in plan['openings']:
    with (ROOT/opening['source']).open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert [int(r['output_index']) for r in rows[:12]] == opening['indices']
with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8', newline='') as f:
    control = list(csv.DictReader(f))
control_stream = [alphabet.index(c) for c in
                  (ROOT/'text/lp2-56.txt').read_text(encoding='utf-8') if c in alphabet]
for i, row in enumerate(control[:56]):
    assert int(row['input_index']) == control_stream[i]
    assert int(row['subtracted_value']) == keys[i]
    assert int(row['output_index']) == (control_stream[i]-keys[i]) % 29
assert control[56]['copied'] == 'True'
expected = {(p, o, s) for p, stream in streams.items() if stream
            for o in plan['offsets'] for s in plan['signs']}
seen = set()
matching = 0
for case in result['cases']:
    identity = (case['page'], case['offset'], case['sign'])
    assert identity in expected and identity not in seen
    seen.add(identity)
    output = case['output_indices']
    stream = streams[case['page']]
    assert len(output) == len(stream)
    for i, value in enumerate(output):
        assert type(value) is int and 0 <= value < 29
        # Undo the stored transformation, rather than call the runner's decoder.
        assert (value-case['sign']*keys[case['offset']+i]) % 29 == stream[i]
    matches = [o['id'] for o in plan['openings'] if output[:12] == o['indices']]
    assert case['matching_openings'] == matches
    matching += bool(matches)
assert seen == expected
assert result['case_count'] == len(expected) == 3190
assert result['comparison_count'] == len(expected)*len(plan['openings']) == 28710
assert result['matching_case_count'] == matching
print('Independent audit: all 3190 candidates; nine source openings; 56-rune known control passed.')
