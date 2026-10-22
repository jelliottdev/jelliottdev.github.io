"""Independent scope and arithmetic checks for the full affine lag sweep."""
from collections import Counter
import importlib.util
import itertools
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
plan = json.loads((HERE / 'plan.json').read_text(encoding='utf-8'))
result = json.loads((HERE / 'results.json').read_text(encoding='utf-8'))
alphabet = json.loads((ROOT / 'data/index.json').read_text(encoding='utf-8'))['alphabet']
lookup = {entry['rune']: i for i, entry in enumerate(alphabet)}
words = []
for page in plan['source_pages']:
    source = (ROOT / 'text' / f'{page}.txt').read_text(encoding='utf-8')
    for piece in re.split(r'[-.]', source):
        word = [lookup[char] for char in piece if char in lookup]
        if word:
            words.append(word)
assert len(words) == result['word_count']
assert sum(map(len, words)) == result['rune_count']
for lag in plan['lags']:
    pairs = [(word[i], word[i+lag]) for word in words for i in range(max(0, len(word)-lag))]
    assert len(pairs) == result['opportunities_by_lag'][str(lag)]
    if lag == 6:
        matches = sum((27*x+24) % 29 == y for x, y in pairs)
        assert matches == result['supplied_lag_six_rule']['matches'] == 77

# Verify the shuffle expectation function against all distinct orders of a
# small word. This checks the combinatorial subtraction for equal runes.
spec = importlib.util.spec_from_file_location('affine_lag_sweep', HERE / 'run.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
toy = [0, 0, 1, 2]
orders = sorted(set(itertools.permutations(toy)))
for lag in (1, 2):
    expected = module.expected_matrix([toy], lag)
    observed = Counter((order[i], order[i+lag]) for order in orders
                       for i in range(len(toy)-lag))
    for x in range(29):
        for y in range(29):
            assert abs(expected[x][y] - observed[(x,y)]/len(orders)) < 1e-12

null = result['selection_null']
assert len(null['maxima']) == null['trials'] == plan['trials']
assert result['candidate_count'] == len(plan['lags']) * 29 * 29
assert null['p_plus_one'] == (null['exceedances']+1)/(null['trials']+1)
assert max(result['selected_by_lag'], key=lambda row: row['score'])['lag'] == result['selected']['lag']
print('PASS independent word/pair totals, supplied relation, exact shuffle mean and saved tail arithmetic')
