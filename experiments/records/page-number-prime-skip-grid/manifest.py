"""Freeze assigned linear keys and exact signed-array control representatives."""
import hashlib
import engine as e


def main():
    assignments=e.assignments()
    signed={}
    for row in assignments:
        for sign in (-1,1):
            pair=(sign*row['slope']%29,sign*row['intercept']%29)
            signed.setdefault(pair,{**row,'sign':sign,'signed_slope':pair[0],'signed_intercept':pair[1]})
    assert len(assignments)==165 and len({(r['slope'],r['intercept']) for r in assignments})==56
    assert len(signed)==112
    for i in range(55):
        p=next(r for r in assignments if r['mode']=='prime' and r['source_index']==i)
        t=next(r for r in assignments if r['mode']=='totient' and r['source_index']==i)
        assert p['key_sha256']!=t['key_sha256']
    controls=[]
    for ordinal,(pair,representative) in enumerate(sorted(signed.items())):
        controls.append(representative|{'control_ordinal':ordinal,'reading':'warning' if ordinal%2==0 else 'lp2-56'})
    e.write(e.HERE/'key-manifest.json',{'assignments':assignments,'signed_control_representatives':controls,
        'base_arrays':56,'signed_arrays':112,'assigned_target_labels':165,'target_settings':660,
        'key_length':1124,'source_index50_maps_to':'lp2-51',
        'linear_skip_proof':'K[j]=B+D*j with nonzero signed slope D. Two rejected consecutive keys would require equal consecutive key values, impossible. One-key skip is admissible iff Cprev-Ccur=D mod29, independent of pointer/intercept. Thus source max3 permits only0or1 actual skipped draw here.',
        'finite_bounds':'Generic guard4*277+8=1116<1124. Linear admissibility sharpens maximum consumed key index to2*(277-1)=552.',
        'control_equivalence':'For inverse-planted known text and fixed seed, changing the ramp intercept only translates ciphertext. Signed-slope/reading pairs, not112labels, determine distinct planted decoder problems; report observed signatures.'})
    print('165assigned labels;56base arrays;112signed representatives;660target settings')


if __name__=='__main__':
    main()
