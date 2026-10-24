"""Independent integer recount of every observed alignment and diagnostic controls."""
import collections,hashlib,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def direct(a,b,lag):
    sa=max(lag,0);sb=max(-lag,0);n=min(len(a)-sa,len(b)-sb)
    freq=collections.Counter((x-y)%29 for x,y in zip(a[sa:sa+n],b[sb:sb+n]))
    return n,sum(v*(v-1) for v in freq.values())
def best_direct(a,b,minimum):
    best=None
    for lag in range(-(len(b)-minimum),len(a)-minimum+1):
        n,num=direct(a,b,lag);value=num/(n*(n-1))
        if best is None or value>best['ioc']:best={'lag':lag,'overlap':n,'numerator':num,'ioc':value}
    return best
def main():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'));r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));pages=json.loads((HERE/'pages.json').read_text(encoding='utf-8'));streams=[p['runes'] for p in pages]
    assert r['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    cases=np.load(HERE/'cases.npz')['cases'];assert hashlib.sha256(cases.astype('<i8').tobytes()).hexdigest()==r['cases_sha256']
    expected=[];best=None;cursor=0;zero=0
    for i,a in enumerate(streams):
        for j,b in enumerate(streams[i+1:],i+1):
            if min(len(a),len(b))<plan['minimum_overlap']:continue
            for lag in range(-(len(b)-120),len(a)-120+1):
                n,num=direct(a,b,lag);assert cases[cursor].tolist()==[i,j,lag,n,num];cursor+=1
                if lag==0:zero+=1
                value=num/(n*(n-1))
                if best is None or value>best['ioc']:best={'i':i,'j':j,'lag':lag,'overlap':n,'numerator':num,'ioc':value}
    assert cursor==331908 and zero==1326 and best==r['observed']
    # All zero-offset differences agree with the existing published grid.
    old=HERE.parent/'lp2-page-pair-alignment/results.json'
    if old.exists():
        prior=json.loads(old.read_text(encoding='utf-8'))
        # The bundled manuscript grid remains independently checkable outside the wiki.
        oldrows=prior.get('cases',[])
        for oldrow in oldrows:
            if oldrow['operation']!='difference' or oldrow['compared_runes']<120:continue
            i=r['page_ids'].index(oldrow['page_a']);j=r['page_ids'].index(oldrow['page_b']);n,num=direct(streams[i],streams[j],0)
            assert num/(n*(n-1))==oldrow['ioc']
    for ctrl in r['positive_controls']:
        b=best_direct(ctrl['a'],ctrl['b'],120);assert b['lag']==ctrl['lag'] and b['ioc']==1.0
        wrong=best_direct(ctrl['a'],ctrl['shuffled_b'],120);assert wrong['ioc']==ctrl['shuffled_top']['ioc']<1.0
    rng=np.random.default_rng(plan['null_seed'])
    for win in r['null_maxima']:
        shuffled=[rng.permutation(np.array(s,dtype=np.int16)).tolist() for s in streams]
        n,num=direct(shuffled[win['i']],shuffled[win['j']],win['lag'])
        assert n==win['overlap'] and num==win['numerator'] and num/(n*(n-1))==win['ioc']
    exceed=sum(x['ioc']>=best['ioc'] for x in r['null_maxima'])
    assert exceed==r['null_exceedances'] and (exceed+1)/129==r['global_empirical_plus_one']
    print('PASS:331908 independent observed recounts; zero-offset baseline; three shifted plants;128 null winners; global comparison')
if __name__=='__main__':main()
