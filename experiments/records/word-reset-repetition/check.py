"""Independent regex tokenizer and multiplicity-vector comparison."""
import json,re
from collections import Counter,defaultdict
from itertools import product,permutations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
r=json.loads((ROOT/'exports/word-reset-bound.json').read_bytes())
alphabet=json.loads((ROOT/'data/index.json').read_bytes())['alphabet']
lookup={a['rune']:i for i,a in enumerate(alphabet)}
for policy in r['policies']:
    transparent='/\r\n'+("'" if policy['apostrophe']=='transparent' else '')
    pattern=re.compile('['+re.escape(''.join(lookup)+transparent)+']+')
    selected=[]; counts=[]
    for n in range(56):
        page=f'lp2-{n:02}'
        raw=json.loads((ROOT/f'data/pages/{page}.json').read_bytes())['raw']
        tokens=[]
        for match in pattern.finditer(raw):
            offsets=[i for i in range(match.start(),match.end()) if raw[i] in lookup]
            if offsets:tokens.append(dict(indices=[lookup[raw[i]] for i in offsets],source_offsets=offsets))
        interior=tokens[1:-1]
        counts.append(dict(page=page,all_tokens=len(tokens),interior_tokens=len(interior),selected_ge4=sum(len(t['indices'])>=4 for t in interior)))
        selected += [dict(page=page,token_index=i,**t) for i,t in enumerate(interior,1) if len(t['indices'])>=4]
    assert selected==policy['tokens'] and counts==policy['page_counts']
    exact=Counter(tuple(t['indices']) for t in selected)
    profiles=defaultdict(list)
    for t in selected:
        # A vector of counts in alphabet order, not sorted-symbol signatures.
        c=Counter(t['indices']);v=tuple(c[i] for i in range(29))
        profiles[v].append(dict(page=t['page'],token_index=t['token_index']))
    collision_groups=[x for x in profiles.values() if len(x)>1]
    assert sorted(collision_groups,key=repr)==sorted([g['occurrences'] for g in policy['anagram_collisions']],key=repr)
    assert len(selected)==policy['selected_tokens']==policy['distinct_exact']==len(exact)
    assert sum(v*(v-1)//2 for v in exact.values())==policy['exact_pairs']==0
    assert sum(len(v)*(len(v)-1)//2 for v in profiles.values())==policy['anagram_pairs_ge4']==4
    assert sum(len(v)*(len(v)-1)//2 for k,v in profiles.items() if sum(k)>=5)==policy['anagram_pairs_ge5']==0
    assert policy['exact_collisions']==[]
    for g in policy['anagram_collisions']:
        assert g['pairs']==len(g['occurrences'])*(len(g['occurrences'])-1)//2
        for loc in g['occurrences']:
            t=next(t for t in selected if t['page']==loc['page'] and t['token_index']==loc['token_index'])
            assert Counter(t['indices'])==Counter(g['signature'])
assert [p['selected_tokens'] for p in r['policies']]==[1589,1591]
controls=0
for w in product(range(3),repeat=3):
    for mapping in product(range(3),repeat=3):
        mapped=tuple(mapping[i] for i in w)
        for order in permutations(range(3)):
            assert Counter(mapped)==Counter(mapped[i] for i in order)
            controls+=1
# Changing context can hide repetitions: same input, different shift.
w=(0,1,0)
assert tuple((i+1)%29 for i in w)!=tuple((i+2)%29 for i in w)
assert Counter((0,1,0))!=Counter((2,3,2))
print(f'PASS: independent tokenization and collision groups; {controls} arbitrary-map/permutation controls')
