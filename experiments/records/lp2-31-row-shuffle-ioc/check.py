"""Independent position-pair checks for observed scores and three shuffle trials."""
import json
import random
from fractions import Fraction
from collections import Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
p=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
baseline=json.loads((HERE.parent/'lp2-31-periodic-ioc/results.json').read_text(encoding='utf-8'))
alphabet={x['rune'] for x in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
rows=[[c for c in line if c in alphabet] for line in (ROOT/'text/lp2-31.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
assert [len(row) for row in rows]==r['row_lengths']==[23,22,24,24,22,22,21,22,21,24,22,22]
assert r['observed']==baseline['observed']
def oracle(stream,k):
    pairs=[(i,j) for i in range(len(stream)) for j in range(i) if (i-j)%k==0]
    return 2*sum(stream[i]==stream[j] for i,j in pairs),2*len(pairs)
stream=sum(rows,[])
for score in r['observed']:
    assert oracle(stream,score['period'])==(score['numerator'],score['denominator'])
rng=random.Random(p['seed'])
for trial in r['null_trials'][:3]:
    shuffled=[]
    for original in rows:
        row=original.copy();rng.shuffle(row)
        assert Counter(row)==Counter(original)
        shuffled.extend(row)
    scores=[oracle(shuffled,k) for k in p['periods']]
    assert trial['numerators']==[n for n,d in scores]
    assert Fraction(trial['max_numerator'],trial['max_denominator'])==max(Fraction(n,d) for n,d in scores)
assert r['exceedances']==sum(t['at_least_observed'] for t in r['null_trials'])
print('Observed scores unchanged; row boundaries and first three null trials pass the pair oracle.')
print('The complete run.py --check verifies all 999 trial records separately.')
