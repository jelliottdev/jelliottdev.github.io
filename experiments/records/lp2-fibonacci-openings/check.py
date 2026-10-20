"""Independent fast-doubling Fibonacci and inverse-arithmetic audit."""
import csv
import hashlib
import json
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
def pair(n):
    if n == 0:
        return 0, 1
    a, b = pair(n // 2)
    c, d = a * (2*b-a), a*a+b*b
    return (d, c+d) if n % 2 else (c, d)

keys = [pair(i)[0] for i in range(max(map(len, streams.values())) + max(plan['offsets']))]
assert result['shifts'] == keys
assert keys[:6] == [0, 1, 1, 2, 3, 5]
states = [(keys[i] % 29, keys[i+1] % 29) for i in range(15)]
assert states[14] == states[0] == (0, 1)
assert len(set(states[:14])) == 14
assert result['residue_period'] == 14
assert result['residue_cycle'] == [s[0] for s in states[:14]]
assert result['page_lengths'] == {p: len(s) for p, s in streams.items()}
assert result['empty_pages'] == [p for p, s in streams.items() if not s]
for opening in plan['openings']:
    with (ROOT/opening['source']).open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert [int(r['output_index']) for r in rows[:12]] == opening['indices']
assert [(c-k) % 29 for c, k in zip([25,11,22,15], keys)] == [25,10,21,13]
baseline_plan = json.loads((HERE.parent/'lp2-prime-minus-one-openings/plan.json').read_text(encoding='utf-8'))
for field in ['pages', 'offsets', 'signs', 'prefix_length', 'openings', 'representation', 'advancement', 'decision', 'stopping_rule']:
    assert plan[field] == baseline_plan[field], field
case_map = {(c['page'],c['offset'],c['sign']): c for c in result['cases']}
expected = {(p, o, s) for p, stream in streams.items() if stream
            for o in plan['offsets'] for s in plan['signs']}
seen = set()
matching = 0
for case in result['cases']:
    identity = (case['page'], case['offset'], case['sign'])
    assert identity in expected and identity not in seen
    seen.add(identity)
    assert case['output_indices'] == case_map[(case['page'],case['offset'] % 14,case['sign'])]['output_indices']
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
distinct = sum(len({tuple(c['output_indices']) for c in result['cases'] if c['page'] == p}) for p in streams)
assert result['distinct_page_outputs'] == distinct == 1540
print('Independent audit: 3190 cases, 1540 distinct page outputs, all match decisions, and exact period 14 verified.')
