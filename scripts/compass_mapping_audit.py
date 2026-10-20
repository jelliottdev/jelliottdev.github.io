"""Enumerate explicitly bounded index maps; no image alignment or decryption claim."""
import argparse
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'exports/compass-mapping-audit.json'

def report():
    maps=[dict(a=a,b=b,table=[(a*x+b)%29 for x in range(29)]) for a in range(1,29) for b in range(29)]
    one=[m for m in maps if m['table'][24]==4]
    two=[m for m in one if m['table'][4]==24]
    # Algebraic cross-check: each nonzero slope determines exactly one offset.
    assert {(m['a'],m['b']) for m in one}=={(a,(4-24*a)%29) for a in range(1,29)}
    slope=((24-4)*pow(4-24,-1,29))%29
    offset=(4-24*slope)%29
    assert [(m['a'],m['b']) for m in two]==[(slope,offset)]
    assert len({tuple(m['table']) for m in maps})==812
    assert all(len(set(m['table']))==29 for m in maps)
    atbash=next(m for m in two)
    shift=next(m for m in one if m['a']==1)
    return dict(scope='All maps y=a*x+b modulo 29 with 1<=a<=28, 0<=b<=28; selected correspondences are mathematical examples, not measured image points.',
                affine_map_count=len(maps),one_pair=dict(constraints=[[24,4]],count=len(one),maps=one,arbitrary_permutation_count=math.factorial(28)),
                two_pairs=dict(constraints=[[24,4],[4,24]],count=len(two),maps=two,arbitrary_permutation_count=math.factorial(27)),
                examples=[dict(input=x,atbash=atbash['table'][x],shift_plus9=shift['table'][x]) for x in [0,4,14,24,28]],
                atbash_fixed_indices=[x for x in range(29) if atbash['table'][x]==x],
                limitation='Does not reproduce the proposed cover-pointer geometry, Albam/Achbi tables or marginalia-based instructions. No unsolved page is decrypted.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();r=report()
    if args.check:
        assert r==json.loads(OUTPUT.read_text(encoding='utf-8'))
        print('PASS: 812 maps; 28 fit one pair; one affine map fits the two specified pairs')
    else: print(json.dumps(r,indent=2))
