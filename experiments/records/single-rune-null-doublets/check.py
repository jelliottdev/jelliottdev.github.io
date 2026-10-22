"""Independent check using regex streams and deletion-bridge accounting."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
runes={entry['rune'] for entry in alphabet}
pattern=re.compile('['+''.join(sorted(runes))+']')
pages=[''.join(pattern.findall((ROOT/f'text/lp2-{n:02d}.txt').read_text(encoding='utf-8'))) for n in range(56)]
baseline=sum(sum(a==b for a,b in zip(page,page[1:])) for page in pages)
assert baseline==data['baseline']['doublets']==86
assert sum(map(len,pages))==12956

for entry, row in zip(alphabet,data['variants']):
    symbol=entry['rune']
    assert row['rune']==symbol and row['label']==entry['latin']
    reduced=[re.sub(re.escape(symbol),'',page) for page in pages]
    lost=sum(sum(page[i]==page[i+1]==symbol for i in range(len(page)-1)) for page in pages)
    bridges=0
    for page in pages:
        # Each internal nonempty segment pair separated by one or more deleted runes
        # contributes a bridge exactly when its touching survivors are equal.
        segments=re.split(f'{re.escape(symbol)}+',page)
        bridges+=sum(bool(left and right and left[-1]==right[0])
                     for left,right in zip(segments,segments[1:]))
    observed=sum(sum(a==b for a,b in zip(page,page[1:])) for page in reduced)
    edges=sum(max(0,len(page)-1) for page in reduced)
    expected=sum((Fraction(sum(v*(v-1) for v in Counter(page).values()),len(page))
                  for page in reduced if page),Fraction())
    assert row['old_doublets_removed']==lost
    assert row['new_bridge_doublets']==bridges
    assert observed==baseline-lost+bridges==row['doublets']
    assert row['deleted']==sum(page.count(symbol) for page in pages)
    assert row['runes']==12956-row['deleted']
    assert row['edges']==edges
    assert Fraction(row['doublet_rate'])==Fraction(observed,edges)
    assert Fraction(row['fixed_count_shuffle_expectation'])==expected
assert all(row['doublets']>baseline for row in data['variants'])
print('PASS: all 29 deletions, bridge identities, edges and exact shuffle expectations independently reproduce')
