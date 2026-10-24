"""Independently verify plants and measured comparison domains from source-call traces."""
import hashlib,json,random
from pathlib import Path
HERE=Path(__file__).resolve().parent
def recovery(a,b):return sum(x==y for x,y in zip(a,b))/min(len(a),len(b))
def main():
    d=json.loads((HERE/'results.json').read_text());p=json.loads((HERE/'plan.json').read_text())
    assert d['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    plants={(x['seed'],x['suppression']):x for x in d['plants']};assert len(plants)==6
    for (seed,supp),plant in plants.items():
        rng=random.Random(seed);K=[rng.randrange(29) for _ in range(2000)];assert K==plant['key_idx']
        # Independent direct construction, tracking accepted positions only.
        toss=random.Random(seed+100);out=[];skips=[];ptr=0
        for value in plant['truth_idx']:
            count=0
            while out and (value+K[ptr])%29==out[-1] and toss.random()<supp:
                ptr+=1;count+=1
            out.append((value+K[ptr])%29);ptr+=1;skips.append(count)
        assert out==plant['cipher_idx'] and skips==plant['encoder_skips']
        assert recovery(plant['full_idx'],plant['truth_idx'])==plant['full_recovery']==1.0
    assert len(d['rows'])==30
    for row in d['rows']:
        plant=plants[row['seed'],row['suppression']];C=plant['cipher_idx'];F=plant['full_idx'];k=row['k']
        ends=[round(240*i/k) for i in range(k+1)]
        # All campaign fold counts divide 240 exactly.
        assert [(f['lo'],f['hi']) for f in row['folds']]==list(zip(ends,ends[1:]))
        vals=[];compared=set()
        for fold in row['folds']:
            lo,hi=fold['lo'],fold['hi'];calls=fold['calls']
            if hi==240:
                assert fold['recovery'] is None and calls==[];continue
            assert len(calls)==2
            pref,tail=calls
            assert pref['cipher_idx']==C[:hi] and pref['offset']==0
            assert tail['cipher_idx']==C[hi:] and tail['offset']==pref['ptr_end']+1
            score=recovery(tail['plain_idx'],F[hi:]);assert score==fold['recovery']==1.0
            head_changed=[(x+1)%29 if i<40 else x for i,x in enumerate(F)]
            all_changed=[(x+1)%29 for x in F]
            assert recovery(tail['plain_idx'],head_changed[hi:])==fold['head40_changed_recovery']==1.0
            assert recovery(tail['plain_idx'],all_changed[hi:])==fold['all_changed_recovery']==0.0
            compared.update(range(hi,240));vals.append(score)
        assert len(vals)==k-1 and compared==set(range(240//k,240))
        want={'min':min(vals),'mean':sum(vals)/len(vals),'frac_pass':sum(v>=.9 for v in vals)/len(vals)}
        assert row['aggregations']==want
    print('PASS: independent plant reconstruction, 30 fold domains, 90 aggregates and diagnostic-reference controls')
if __name__=='__main__':main()
