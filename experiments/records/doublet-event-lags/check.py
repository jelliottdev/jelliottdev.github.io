"""Independent regex extraction and direct pair recount; standard library only."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[3]
r=json.loads(Path(__file__).with_name('results.json').read_text())
alphabet=[a['rune'] for a in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']]
events=[]
for page in range(56):
    name=f'lp2-{page:02d}'
    text=(ROOT/f'text/{name}.txt').read_text(encoding='utf-8')
    stream=''.join(c for c in text if c in alphabet)
    for m in re.finditer(r'(?=(.)\1)',stream):
        events.append(dict(page=name,rune_index=m.start(),value=alphabet.index(m.group(1))))
assert events==r['events']
for row in r['lags']:
    lag=row['lag']; pairs=[];hist=[0]*29;dist=[]
    for j in range(lag,len(events)):
        a,b=events[j-lag],events[j]
        delta=b['value']-a['value']
        if delta<0: delta+=29
        hist[delta]+=1
        dist.append(min(abs(b['value']-a['value']),29-abs(b['value']-a['value'])))
        pairs.append(dict(left=j-lag,right=j,directed=delta,crosses_page=a['page']!=b['page']))
    assert pairs==row['pairs'] and hist==row['directed_histogram']
    assert len(pairs)==row['pair_count'] and sum(x['crosses_page'] for x in pairs)==row['cross_page_count']
    assert sum(dist)==row['circular_sum'] and str(Fraction(sum(dist),len(dist)))==row['circular_mean']
    assert hist[4]==row['plus4_count'] and str(Fraction(hist[4],len(dist)))==row['plus4_rate']
    assert sum(x in (5,12,14) for x in dist)==row['distance_5_12_14_count']
counts=Counter(e['value'] for e in events);n=len(events)
expected=[str(Fraction(sum(c*(counts[(a+d)%29]-(d==0)) for a,c in counts.items()),n*(n-1))) for d in range(29)]
assert expected==r['shuffle_directed_probabilities'] and expected[4]==r['shuffle_plus4_probability']
print('PASS: independent extraction, all pairs and frequency-based expectations')
