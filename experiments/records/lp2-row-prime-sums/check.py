"""Independent trial-division audit of observed rows and three seeded null trials."""
import itertools
import json
import math
from pathlib import Path
import random
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
p=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
def prime(n):return n>=2 and all(n%d for d in range(2,math.isqrt(n)+1))
assert [prime(n) for n in (0,1,2,3,4,49,97,121)]==[False,False,True,True,False,False,True,False]
values={x['rune']:x['prime'] for x in r['alphabet']}
sources=[]
for page in r['observed']:
    rows=[];numbers=[]
    for line_no,line in enumerate((ROOT/'text'/(page['page']+'.txt')).read_text(encoding='utf-8').splitlines(),1):
        row=[values[c] for c in line if c in values]
        if row:rows.append(row);numbers.append(line_no)
    assert page['rows']==[{'line':n,'runes':len(row),'sum':sum(row),'prime':prime(sum(row))} for n,row in zip(numbers,rows)]
    sources.append(rows)
assert sum(len(rows) for rows in sources)==r['row_count']
assert sum(prime(sum(row)) for rows in sources for row in rows)==r['prime_row_count']
rng=random.Random(p['seed'])
for trial in r['null_trials'][:3]:
    counts=[]
    for rows in sources:
        flat=list(itertools.chain.from_iterable(rows));rng.shuffle(flat);iterator=iter(flat)
        counts.append(sum(prime(sum(itertools.islice(iterator,len(row)))) for row in rows))
        assert list(iterator)==[]
    assert counts==trial['page_counts'] and sum(counts)==trial['total']
for trial in r['null_trials']:
    assert len(trial['page_counts'])==len(p['pages'])
    assert trial['total']==sum(trial['page_counts'])
    assert trial['at_least_observed']==(trial['total']>=r['prime_row_count'])
assert r['exceedances']==sum(t['at_least_observed'] for t in r['null_trials'])
assert r['monte_carlo_p']==(1+r['exceedances'])/(1+len(r['null_trials']))
print('All observed sums pass trial division; first three null datasets and all trial totals agree.')
