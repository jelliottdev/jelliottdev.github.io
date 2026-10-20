"""Independent pairwise-gap check from page JSON and stride controls."""
import json
from itertools import combinations
from functools import reduce
from math import gcd
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
saved=json.loads((ROOT/'exports/position-divisor-bound.json').read_bytes())
alphabet=json.loads((ROOT/'data/index.json').read_bytes())['alphabet']
labels={a['rune']:a['latin'] for a in alphabet}
rows={r['page']:r for r in saved['pages']}
empty=[]
for n in range(56):
    page=f'lp2-{n:02}'
    raw=json.loads((ROOT/f'data/pages/{page}.json').read_bytes())['raw']
    stream=[c for c in raw if c in labels]
    if not stream:
        empty.append(page)
        continue
    r=rows[page]
    assert r['rune_count']==len(stream)
    assert {d['rune'] for d in r['runes']}==set(stream)
    for d in r['runes']:
        positions=[i for i,c in enumerate(stream) if c==d['rune']]
        assert positions==d['positions'] and labels[d['rune']]==d['label']
        # All pairwise gaps, instead of only distances from the first occurrence.
        g=reduce(gcd,(b-a for a,b in combinations(positions,2)),0)
        assert g==d['gap_gcd']
        triple=d['triple_witness']
        if triple is not None:
            assert len(triple)==3 and triple==sorted(set(triple))
            assert all(i in positions for i in triple)
            assert gcd(triple[1]-triple[0],triple[2]-triple[0])==1
    assert r['gcd_one_labels']==[d['label'] for d in r['runes'] if d['gap_gcd']==1]
    assert r['gcd_one_labels'] and r['excludes_unit_stride']
    # Counterexample to an unrestricted-stride rejection: q=2 for all
    # labels, N=2 and s=2 satisfies divisibility at every position.
    assert all((2+2*i)%2==0 for i in range(len(stream)))
assert len(rows)==saved['excluded_unit_stride_pages']==55
assert empty==saved['skipped_empty_pages']==['lp2-50']
# A valid unit-stride pattern: label A at positions 0,2,4 has q=2,N=2.
assert all((2+i)%2==0 for i in [0,2,4])
assert reduce(gcd,(b-a for a,b in combinations([0,2,4],2)),0)==2
# Synthetic gcd-one gaps: only strides divisible by q can satisfy all
# three positions for some origin. Enumerate residues of N, not guesses.
for q in range(2,20):
    for s in range(-12,13):
        possible=any(all((N+s*i)%q==0 for i in [0,2,5]) for N in range(q))
        assert possible==(s%q==0)
print('PASS: all page-JSON pairwise gaps; 55 stride-two counterexamples; 450 finite residue controls')
