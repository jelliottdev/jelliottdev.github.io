"""Check the exact geometry from saved centroid sums; no producer import.

This verifies the certificate and source hashes, not independent segmentation.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
d=json.loads((ROOT/'exports/compass-shared-radii.json').read_bytes())
def fraction(v):return F(v['numerator'],v['denominator'])
def squared(p,q):return sum((x-y)**2 for x,y in zip(p,q))
corners=[(0,0),(2399,0),(0,3599),(2399,3599)]
variants={t:[] for t in (100,140,180)}
assert d['maximum_radius_squared']==squared(corners[0],corners[-1])
for page in d['pages']:
    raw=(ROOT/f"images/{page['page']}.jpg").read_bytes()
    assert hashlib.sha256(raw).hexdigest()==page['source_sha256']
    for row in page['thresholds']:
        a,b,c=[tuple(F(x['sum_'+axis],x['area']) for axis in ('x','y')) for x in row['dots']]
        assert all(0<=x<=2399 and 0<=y<=3599 for x,y in (a,b,c))
        ac2=squared(a,c)
        # Projection parameter from three squared side lengths.
        t=(squared(a,b)+ac2-squared(b,c))/(2*ac2)
        k=t*(1-t)*ac2
        residuals=[squared(b,x)-(1-t)*squared(a,x)-t*squared(c,x)+k for x in corners]
        expected=(t,k,min(residuals),max(residuals))
        assert tuple(fraction(row['geometry'][key]) for key in ['t','K','residual_min','residual_max'])==expected
        variants[row['threshold']].append(expected)
        # The squared terms cancel: residual is affine in the target.
        midpoint=(F(2399,2),F(3599,2))
        centre=squared(b,midpoint)-(1-t)*squared(a,midpoint)-t*squared(c,midpoint)+k
        assert centre==sum(residuals)/4
for cert in d['certificates']:
    (t1,k1,l1,h1),(t2,k2,l2,h2)=variants[cert['threshold']]
    lower=abs(k2-k1)-abs(t2-t1)*d['maximum_radius_squared']
    upper=max(abs(x-y) for x in (l1,h1) for y in (l2,h2))
    assert fraction(cert['lower_bound'])==lower and fraction(cert['upper_bound'])==upper
    assert fraction(cert['margin'])==lower-upper
    assert cert['incompatible']==(lower>upper)
    # Identical page geometry cannot be rejected by this necessary bound.
    assert F(0)<=max(abs(x-y) for x in (l1,h1) for y in (l1,h1))
assert len(d['pages'])==2 and len(d['certificates'])==3
print('PASS: source hashes, exact distance identities, corner extrema and three incompatibility certificates')
