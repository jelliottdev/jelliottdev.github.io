"""Independent binomial-sum check from page JSON; no census imports."""
import json
from math import comb, gcd
from functools import reduce
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
saved = json.loads((ROOT / 'exports/polynomial-stream-bound.json').read_bytes())
alphabet = json.loads((ROOT / 'data/index.json').read_bytes())['alphabet']
lookup = {a['rune']: (i, a['prime']) for i,a in enumerate(alphabet)}
def direct(values, order):
    return [sum((-1)**(order-k)*comb(order,k)*values[i+k] for k in range(order+1))
            for i in range(len(values)-order)]
expected_keys = set()
empty = []
for n in range(56):
    page = f'lp2-{n:02}'
    raw = json.loads((ROOT / f'data/pages/{page}.json').read_bytes())['raw']
    runes = [c for c in raw if c in lookup]
    if not runes:
        empty.append(page)
        continue
    for label in ('index','prime'):
        for degree in range(1,9): expected_keys.add((page,label,degree))
assert {(r['page'],r['representation'],r['degree_bound']) for r in saved['rows']} == expected_keys
assert len(saved['rows']) == len(expected_keys) == 880
assert empty == saved['skipped_empty_pages'] == ['lp2-50']
for r in saved['rows']:
    raw = json.loads((ROOT / f"data/pages/{r['page']}.json").read_bytes())['raw']
    col = 0 if r['representation']=='index' else 1
    values = [lookup[c][col] for c in raw if c in lookup]
    diffs = direct(values,r['order'])
    assert len(values)==r['runes'] and r['order']==r['degree_bound']+1
    assert diffs==r['differences']
    assert reduce(gcd,diffs,0)==r['gcd']==1
    assert diffs[:len(r['prefix_witness'])]==r['prefix_witness']
    assert reduce(gcd,r['prefix_witness'],0)==1
    assert r['excluded_all_moduli_gt_one'] is True
# Positive controls: polynomial outputs reduced mod m must pass the
# necessary divisibility condition, including negative origin and stride.
controls = 0
for degree in range(1,9):
    for m in (2,28,29,114):
        for origin,stride in ((0,1),(-7,3),(11,-2),(5,0)):
            values = [sum((j+1)*(origin+stride*i)**j for j in range(degree+1)) % m for i in range(25)]
            assert all(x % m == 0 for x in direct(values,degree+1))
            controls += 1
assert direct([0,1,4,9,16],3)==[0,0]
assert direct([0,1,4,9,17],3)==[0,1]
assert saved['checks']==saved['excluded_checks']==880
print(f'PASS: 880 binomial-formula checks from page JSON; {controls} polynomial controls; perturbed-square control')
