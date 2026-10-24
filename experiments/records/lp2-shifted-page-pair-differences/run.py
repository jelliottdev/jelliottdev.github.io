"""Complete bounded shifted page-pair IoC grid with shared-page shuffle maxima."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def load():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'));raw=(HERE/'pages.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==plan['pages_sha256']
    pages=json.loads(raw);return plan,[p['id'] for p in pages],[np.array(p['runes'],dtype=np.int16) for p in pages]
def pair_counts(a,b,minimum):
    lags=np.arange(-(len(b)-minimum),len(a)-minimum+1,dtype=np.int32)
    sa=np.maximum(lags,0);sb=np.maximum(-lags,0)
    lengths=np.minimum(len(a)-sa,len(b)-sb);positions=np.arange(int(lengths.max()))
    good=positions[None,:]<lengths[:,None]
    ai=np.minimum(sa[:,None]+positions[None,:],len(a)-1)
    bi=np.minimum(sb[:,None]+positions[None,:],len(b)-1)
    values=(a[ai]-b[bi])%29
    labels=values+29*np.arange(len(lags))[:,None]
    counts=np.bincount(labels[good],minlength=29*len(lags)).reshape(-1,29)
    numerators=(counts*(counts-1)).sum(axis=1)
    return lags,lengths,numerators
def grid(streams,minimum,save=False):
    top=None;arrays=[]
    for i,a in enumerate(streams):
        for j in range(i+1,len(streams)):
            b=streams[j]
            if min(len(a),len(b))<minimum:continue
            lags,ns,nums=pair_counts(a,b,minimum);den=ns*(ns-1);scores=nums/den
            ix=int(scores.argmax());candidate={'i':i,'j':j,'lag':int(lags[ix]),'overlap':int(ns[ix]),'numerator':int(nums[ix]),'ioc':float(scores[ix])}
            if top is None or candidate['ioc']>top['ioc']:top=candidate
            if save:arrays.append(np.column_stack((np.full(len(lags),i),np.full(len(lags),j),lags,ns,nums)))
    return top,np.concatenate(arrays).astype(np.int64) if save else None
def controls(plan):
    rng=np.random.default_rng(plan['positive_controls']['seed']);rows=[]
    for lag in plan['positive_controls']['lags']:
        a=rng.integers(0,29,277,dtype=np.int16);b=rng.integers(0,29,277,dtype=np.int16)
        sa=max(lag,0);sb=max(-lag,0);n=min(277-sa,277-sb);b[sb:sb+n]=(a[sa:sa+n]-7)%29
        top,_=grid([a,b],120);assert top['ioc']==1.0 and top['lag']==lag
        wrong=b.copy();rng.shuffle(wrong);wrongtop,_=grid([a,wrong],120);assert wrongtop['ioc']<1.0
        rows.append({'lag':lag,'a':a.tolist(),'b':b.tolist(),'top':top,'shuffled_b':wrong.tolist(),'shuffled_top':wrongtop})
    return rows
def generate():
    plan,ids,streams=load();ctrl=controls(plan);observed,cases=grid(streams,plan['minimum_overlap'],True)
    assert len(cases)==plan['cell_count'] and int((cases[:,2]!=0).sum())==plan['nonzero_lag_cells']
    rng=np.random.default_rng(plan['null_seed']);nulls=[]
    for t in range(plan['null_trials']):
        shuffled=[rng.permutation(s) for s in streams];top,_=grid(shuffled,plan['minimum_overlap']);nulls.append(top)
        if (t+1)%16==0:print(f'null grids {t+1}/{plan["null_trials"]}',flush=True)
    exceed=sum(x['ioc']>=observed['ioc'] for x in nulls)
    return {'schema':'shifted-page-differences-v1','plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),'page_ids':ids,'eligible_pages':plan['eligible_pages'],'pair_count':plan['pair_count'],'cell_count':len(cases),'nonzero_lag_cells':int((cases[:,2]!=0).sum()),'observed':observed,'null_maxima':nulls,'null_exceedances':exceed,'global_empirical_plus_one':(exceed+1)/(len(nulls)+1),'positive_controls':ctrl,'cases_sha256':hashlib.sha256(cases.astype('<i8').tobytes()).hexdigest(),'interpretation':'Finite actual manuscript alignment search; concentration statistic only; no general shared-key or plaintext-family exclusion.'},cases
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();result,cases=generate()
    if args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'));assert np.array_equal(cases,np.load(HERE/'cases.npz')['cases']);print('PASS: full manuscript and128-null-grid replay')
    else:
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n');np.savez_compressed(HERE/'cases.npz',cases=cases);print(json.dumps({k:result[k] for k in ['cell_count','observed','null_exceedances','global_empirical_plus_one']}))
