import argparse,hashlib,importlib.util,json,math,sys,time
from pathlib import Path
import numpy as np
from numba import njit
HERE=Path(__file__).resolve().parent;SPACE=26**4
@njit
def decode(C,k,a,b,c,seed,sign):
    P=np.empty(len(C),np.int64)
    for i in range(len(C)):
        f=0
        if i>=k:
            f=a*C[i-1]
            if k>=2:f+=b*C[i-2]
            if k>=3:f+=c*C[i-3]
        P[i]=(C[i]+sign*(seed+f))%29
    return P
@njit
def score(P,letters,sizes,table):
    state=0;chars=0;total=0.
    for r in P:
        for j in range(sizes[r]):
            state=(state*26+letters[r,j])%SPACE;chars+=1
            if chars>=4:total+=table[state]
    return total/(chars-3) if chars>3 else -999.
@njit
def grid(C,coeffs,letters,sizes,table):
    out=np.empty((len(coeffs),4),np.float64)
    for j in range(len(coeffs)):
        k,a,b,c=coeffs[j]
        for seed in range(2):
            for s in range(2):out[j,seed*2+s]=score(decode(C,k,a,b,c,seed,-1 if s==0 else 1),letters,sizes,table)
    return out
def setup():
    plan=json.loads((HERE/'frozen-plan.json').read_text(encoding='utf-8'))
    for p in plan['inputs']:assert hashlib.sha256((HERE/p['path']).read_bytes()).hexdigest()==p['sha256']
    labels=json.loads((HERE/'labels.json').read_text(encoding='utf-8'));letters=np.zeros((29,2),np.int64);sizes=np.array(list(map(len,labels)),np.int64)
    for i,t in enumerate(labels):
        for j,ch in enumerate(t):letters[i,j]=ord(ch)-65
    d={q:int(v) for q,v in [line.split() for line in (HERE/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines()]};norm=math.log10(sum(d.values()));table=np.full(SPACE,math.log10(.01)-norm)
    for q,v in d.items():
        idx=0
        for ch in q:idx=idx*26+ord(ch)-65
        table[idx]=math.log10(v)-norm
    coeffs=[]
    coeffs += [[1,a,0,0] for a in range(1,29)]
    coeffs += [[2,a,b,0] for a in range(29) for b in range(29) if a or b]
    coeffs += [[3,a,b,c] for a in range(29) for b in range(29) for c in [0,1,28,2,27] if a or b or c]
    assert len(coeffs)==5072
    return plan,np.array(coeffs,np.int64),letters,sizes,table,labels
def source():
    sys.dont_write_bytecode=True;path=HERE/'source/liber-primus/analysis/campaign18_skip/ctfeedback_coeffs.py';spec=importlib.util.spec_from_file_location('source_d04',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def preflight(plan,coeffs,letters,sizes,table):
    m=source();actual=[]
    for k in [1,2,3]:
        for c in m.coeff_grid(k):actual.append([k]+c[1:]+[0]*(3-k))
    assert np.array_equal(np.array(actual),coeffs)
    rng=np.random.default_rng(plan['preflight']['parity_seed']);rows=[]
    for n in range(52):
        C=rng.integers(0,29,184,dtype=np.int64) if n<48 else np.full(184,n-48,np.int64)
        ix=int(rng.integers(len(coeffs)));k,a,b,c=map(int,coeffs[ix]);seed=n%2;sign=-1 if n%3 else 1
        native,art=m.decode_with_coeffs(C,m.const_seed(seed,4000),k,[0,a,b,c][:k+1],sign,0);P=decode(C,k,a,b,c,seed,sign);fast=score(P,letters,sizes,table)
        assert art['plain_idx']==P.tolist() and abs(native-fast)<=2e-12
        rows.append({'case':n,'coefficient_index':ix,'seed':seed,'sign':sign,'repeat_rune':None if n<48 else n-48,'source_score':native,'accelerated_score':fast,'delta':abs(native-fast)})
    test=rng.integers(0,29,184,dtype=np.int64);grid(test,coeffs,letters,sizes,table);start=time.perf_counter();grid(test,coeffs,letters,sizes,table);elapsed=time.perf_counter()-start
    projected=elapsed*52*33;assert projected<600,(elapsed,projected)
    truth=json.loads((HERE/'warning.json').read_text(encoding='utf-8'));plants=[]
    for seed in [0,1]:
        C=[]
        for i,p in enumerate(truth):C.append((p+seed+(7*C[-1] if i else 0))%29)
        original=m.SR.encipher_ctfeedback(truth,m.const_seed(seed,4000),k=1,coeffs=[0,7],sign=-1,supp=.83,seed=3301);assert C==original
        scores=grid(np.array(C,np.int64),coeffs,letters,sizes,table);true=float(scores[6,seed*2]);best=float(scores.max());P=decode(np.array(C,np.int64),1,7,0,0,seed,-1);unit=float(scores[0,seed*2]);assert P.tolist()==truth and true>-5.2 and true>=best-2e-12 and unit<-5.5
        plants.append({'seed':seed,'cipher_idx':C,'truth_idx':truth,'true_score':true,'best_score':best,'true_rank':1+int((scores>true+2e-12).sum()),'unit_score':unit,'full_grid_settings':int(scores.size)})
    return {'source_parity_cases':rows,'max_score_delta':max(x['delta'] for x in rows),'synthetic_full_grid_seconds':elapsed,'projected_target_plus32_nulls_seconds':projected,'controls':plants}
def winner(scores,coeffs):
    j,arm=np.unravel_index(int(scores.argmax()),scores.shape);return {'coefficient_index':int(j),'coefficients':coeffs[j].tolist(),'seed':int(arm)//2,'sign':-1 if int(arm)%2==0 else 1,'score':float(scores[j,arm])}
def generate():
    plan,coeffs,letters,sizes,table,labels=setup();gate=preflight(plan,coeffs,letters,sizes,table);print(json.dumps({'parity_max_delta':gate['max_score_delta'],'benchmark_seconds':gate['synthetic_full_grid_seconds'],'projected_seconds':gate['projected_target_plus32_nulls_seconds']}),flush=True)
    pages=json.loads((HERE/'pages.json').read_text(encoding='utf-8'));start=time.perf_counter();arrays=[];rows=[]
    for p in pages:
        C=np.array(p['runes'],np.int64);scores=grid(C,coeffs,letters,sizes,table);arrays.append(scores);w=winner(scores,coeffs);w['page']=p['id'];w['runes']=len(C);w['above_gate']=int((scores>=-5.2).sum());rows.append(w)
    arrays=np.array(arrays);observed=max(rows,key=lambda x:x['score']);bestC=next(p['runes'] for p in pages if p['id']==observed['page']);k,a,b,c=observed['coefficients'];P=decode(np.array(bestC,np.int64),k,a,b,c,observed['seed'],observed['sign']);observed=dict(observed,plain_idx=P.tolist(),latin=''.join(labels[int(x)] for x in P));targetsec=time.perf_counter()-start
    rng=np.random.default_rng(plan['null_seed']);nulls=[];ns=time.perf_counter()
    for t in range(plan['null_trials']):
        best=None
        for p in pages:
            C=rng.permutation(np.array(p['runes'],np.int64));s=grid(C,coeffs,letters,sizes,table);w=winner(s,coeffs);w['page']=p['id']
            if best is None or w['score']>best['score']:best=w
        nulls.append(best)
        if (t+1)%8==0:print(f'feedback null grids {t+1}/32',flush=True)
    exceed=sum(x['score']>=observed['score'] for x in nulls)
    result={'schema':'d04-remaining-pages-v1','plan_sha256':hashlib.sha256((HERE/'frozen-plan.json').read_bytes()).hexdigest(),'gate':gate,'page_results':rows,'observed':observed,'settings':int(arrays.size),'above_gate':int((arrays>=-5.2).sum()),'null_maxima':nulls,'null_exceedances':exceed,'global_empirical_plus_one':(exceed+1)/33,'score_array_sha256':hashlib.sha256(arrays.astype('<f8').tobytes()).hexdigest(),'actual_target_seconds':targetsec,'actual_null_seconds':time.perf_counter()-ns}
    return result,arrays
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();r,a=generate()
    if args.check:
        # Only wall-clock measurements vary; preserve and compare every scientific field.
        timing_fields={'synthetic_full_grid_seconds','projected_target_plus32_nulls_seconds','actual_target_seconds','actual_null_seconds'}
        def scientific(value):
            if isinstance(value,dict):return {k:scientific(v) for k,v in value.items() if k not in timing_fields}
            if isinstance(value,list):return [scientific(v) for v in value]
            return value
        expected=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        assert scientific(r)==scientific(expected)
        assert np.array_equal(a,np.load(HERE/'scores.npz')['scores'])
        print('PASS: complete target/control/32-null numerical replay; only four declared timing fields ignored; expected outputs unchanged')
    else:
        (HERE/'results.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');np.savez_compressed(HERE/'scores.npz',scores=a);print(json.dumps({k:r[k] for k in ['settings','above_gate','observed','global_empirical_plus_one','actual_target_seconds','actual_null_seconds']}))
