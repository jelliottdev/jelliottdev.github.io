"""Independent exhaustive cut-mask check; does not import the producer."""
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
values = {a['latin']: a['prime'] for a in json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']}
assert len(result['rows']) == len(plan['candidates']) == 5
for (original, target), row in zip(plan['candidates'], result['rows']):
    word = original.replace('V', 'U')
    expected = set()
    for mask in product([False, True], repeat=len(word)-1):
        cuts = [0] + [i+1 for i, cut in enumerate(mask) if cut] + [len(word)]
        tokens = tuple(word[a:b] for a, b in zip(cuts, cuts[1:]))
        if all(t in values for t in tokens):
            expected.add(tokens)
    actual = {tuple(v['labels']) for v in row['variants']}
    assert actual == expected and len(actual) == len(row['variants'])
    assert (row['word'], row['normalized'], row['target']) == (original, word, target)
    for v in row['variants']:
        assert v['values'] == [values[t] for t in v['labels']]
        assert v['sum'] == sum(v['values'])
        assert v['matches_target'] == (v['sum'] == target)
assert result['segmentation_count'] == sum(len(r['variants']) for r in result['rows'])
assert result['matching_candidates'] == sum(any(v['matches_target'] for v in r['variants']) for r in result['rows'])
print('PASS: independent exhaustive cut masks agree for all five words')
