"""Check every saved candidate using an independent alphabet-walk lookup."""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
r = json.loads((HERE/'results.json').read_text(encoding='utf-8'))
lookup = {c:i for i,c in enumerate(r['alphabet'])}
streams = {p: [lookup[c] for c in (ROOT/'text'/(p+'.txt')).read_text(encoding='utf-8') if c in lookup]
           for p in {c['page'] for c in r['cases']}}
# A WARNING begins A,W,A: the known Atbash control is 4,21,4 -> 24,7,24.
assert r['expected_prefix'][:3] == [24,7,24]
seen = set()
for c in r['cases']:
    key = (c['page'], c['order'], c['multiplier'], c['offset'])
    assert key not in seen
    seen.add(key)
    mapping, value = [], c['offset']
    for _ in range(29):
        mapping.append(value)
        value += c['multiplier']
        if value < 0: value += 29
        if value > 28: value -= 29
    stream = streams[c['page']]
    positions = range(len(stream)) if c['order']=='original' else range(len(stream)-1,-1,-1)
    expected = [mapping[stream[i]] for i in positions]
    assert expected == c['output_indices']
    assert c['matches_prefix'] == (expected[:12] == r['expected_prefix'])
assert len(seen) == 56*2*2*29 == r['case_count']
assert r['match_count'] == sum(c['matches_prefix'] for c in r['cases'])
print('All 6496 complete candidates agree with the independent alphabet-walk oracle.')
