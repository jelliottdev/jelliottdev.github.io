"""Check the saved certificate without importing the producer.

Uses direct modulus ranges instead of divisor generation; also enumerates
all coefficient pairs for m=110..125 as a separate bounded control.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
d = json.loads((ROOT / 'exports/literal-prime-affine.json').read_text())
primes = sorted(a['prime'] for a in json.loads((ROOT / 'data/index.json').read_bytes())['alphabet'])
assert d['palette'] == primes
allowed = set(primes)
anchors = set()
checked = 0
for row in d['finite_anchor_rows']:
    u, v, p = row['u'], row['v'], row['witness_input']
    assert u != v and u in allowed and v in allowed and p in allowed
    assert (u, v) not in anchors
    anchors.add((u, v))
    # Interpolate from input 2 and input 3, without producer coefficients.
    raw = u+(p-2)*(v-u)
    assert raw == row['unreduced_image'] and raw not in allowed
    bound = max(abs(raw-y) for y in primes)
    expected = [m for m in range(110, bound+1) if raw % m in allowed]
    assert expected == row['candidate_moduli']
    for m in expected:
        values = [(u+(x-2)*(v-u)) % m for x in primes]
        assert sorted(values) != primes
        checked += 1
for row in d['exact_integer_maps']:
    u,v = row['u'],row['v']
    assert (u,v) not in anchors
    anchors.add((u,v))
    assert [u+(x-2)*(v-u) for x in primes] == primes
assert anchors == {(u,v) for u in primes for v in primes if u!=v}
assert checked == d['candidate_maps_tested'] and not d['nonidentity_survivors']
for m in range(110,126):
    survivors=[]
    for a in range(m):
        for b in range(m):
            if (2*a+b)%m not in allowed or (3*a+b)%m not in allowed:
                continue
            if sorted((a*p+b)%m for p in primes)==primes:
                survivors.append((a,b))
    assert survivors == [(1,0)], (m,survivors)
assert {(0*p+2)%110 for p in primes} == {2}
assert [(109*p+5)%110 for p in [2,3]] == [3,2]
print('PASS: complete anchor coverage, direct modulus-range certificate, 16 exhaustive coefficient controls, and two scope counterexamples')
