"""Independent arithmetic check using prime-factor totients and direct row assertions."""
import json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def factors(n):
    out={};p=2
    while n>1:
        while n%p==0:out[p]=out.get(p,0)+1;n//=p
        p+=1
    return out
def phi(n):
    result=n
    for p in factors(n):result=result//p*(p-1)
    return result
def mu(n):
    f=factors(n)
    return 0 if any(v>1 for v in f.values()) else (-1)**len(f)
d=json.loads((HERE/'route.json').read_text(encoding='utf-8'));g=d['map_indices'];count=0
for b in d['blocks']:
    node=[g[(r-1)*27+c-1] for r,c in [b['node_outer_cells'][0],b['node_center'],b['node_outer_cells'][1]]]
    key=[node[0],phi(node[1]) if b['center_transform'] else node[1],node[2]]
    assert key==b['key']
    phase=sum(mu(phi(v)) for v in key)%3
    for i,row in enumerate(b['rows']):
        r,c=row['cell'];cipher=g[(r-1)*27+c-1];k=key[(i+phase)%3]
        assert cipher==row['cipher'] and k==row['aligned_key'] and (cipher-k)%29==row['plaintext'];count+=1
# Exhaustive positive-index phi check against coprime counting, including phi(1).
for n in range(1,730):assert phi(n)==sum(math.gcd(n,k)==1 for k in range(1,n+1))
assert mu(1)==1 and mu(4)==0 and mu(6)==1 and mu(30)==-1
print(f'PASS: {len(d["blocks"])} selected blocks, {count} rune subtractions, key-node derivation, 729 totient controls')
