"""Synthetic-only pretarget gate: no LP2 centroid or null-reference queries."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import similarity
import svd_reference
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
def transform(points,index,permutation):
    angle=np.radians((137.5*index)%360);c,s=np.cos(angle),np.sin(angle);R=np.array([[c,-s],[s,c]])
    if index%2:R=R@np.diag([-1.,1.])
    return (3.7*np.asarray(points)@R+np.array([123.,-45.]))[permutation]
def main():
    plan=json.loads((HERE/'matching-plan-frozen.json').read_text(encoding='utf-8'))
    for item in plan['inputs']:assert sha(HERE/item['path'])==item['sha256'],item['path']
    lib=similarity.catalogue_library();rng=np.random.Generator(np.random.PCG64(330120261024));mathrng=np.random.Generator(np.random.PCG64(330120261028));math_rows=[];maxdelta=0.
    # Ninety-six finite synthetic cases, including collinear/near-collinear,
    # symmetric and repeated-point fixtures. No random reference model is run.
    for i in range(96):
        X=mathrng.normal(size=(3,5,2));Y=mathrng.normal(size=(5,2))
        if i%8==0:X[0,:,1]=0;Y[:,1]=0
        if i%8==1:X[0,:,1]*=1e-12
        if i%8==2:X[1,1]=X[1,0]
        if i%8==3:X[2]=np.array([[-1,0],[0,1],[1,0],[0,-1],[0,0]])
        Y=Y*(10.**((i%7)-3))+np.array([13.,-7.])
        fast=similarity.Library(X).all_scores(Y);reference=svd_reference.all_scores(X,Y);delta=float(np.max(np.abs(fast-reference)));maxdelta=max(maxdelta,delta);assert delta<=1e-12,(i,delta)
        math_rows.append({'fixture':i,'registration_scores':int(fast.size),'maximum_delta':delta})
    exact=[];noisy=[];started=time.perf_counter();exact_queries=[]
    for i in range(88):
        permutation=rng.permutation(5);query=transform(lib.points[i],i,permutation);exact_queries.append(query)
        fast=lib.all_scores(query);reference=svd_reference.all_scores(lib.points,query);delta=float(np.max(np.abs(fast-reference)));maxdelta=max(maxdelta,delta);assert delta<=1e-12,(i,delta)
        minima=fast.min(axis=(1,2));best=float(minima.min());own=float(minima[i]);tie=np.flatnonzero(minima<=best+1e-12);assert i in tie and own<=1e-10,(i,own,best)
        own_index=np.unravel_index(int(np.argmin(fast[i])),(120,2));witness=lib.witness(query,i,*own_index);assert witness['normalized_rms']<=1e-10
        exact.append({'candidate':lib.names[i],'own_score':own,'global_score':best,'own_in_tie_set':bool(i in tie),'tie_candidates':[lib.names[j] for j in tie],'svd_maximum_delta':delta,'witness':witness})
    for sigma in [.001,.01]:
        for i in range(88):
            for replicate in range(8):
                query=transform(lib.points[i],i,rng.permutation(5));radius=float(np.sqrt(np.mean(np.sum((query-query.mean(axis=0))**2,axis=1))));query+=rng.normal(scale=sigma*radius,size=(5,2));scores=lib.all_scores(query);minima=scores.min(axis=(1,2));own=float(minima[i]);best=float(minima.min());rank=1+int(np.sum(minima<own-1e-12));noisy.append({'candidate':lib.names[i],'sigma_radius_fraction':sigma,'replicate':replicate,'own_score':own,'global_score':best,'own_rank':rank,'own_in_best_tie_set':own<=best+1e-12,'best_candidates':[lib.names[j] for j in np.flatnonzero(minima<=best+1e-12)]})
    # Benchmarks repeat full-library searches of transformed known patterns.
    # Scores are consumed but no null-reference model/seed or LP2 points used.
    timing=[]
    for i in range(176):
        t=time.perf_counter();result=lib.all_scores(exact_queries[i%88]);timing.append(time.perf_counter()-t);assert result.shape==(88,120,2)
    summary={str(sigma):{'plants':sum(r['sigma_radius_fraction']==sigma for r in noisy),'own_in_best_tie_set':sum(r['sigma_radius_fraction']==sigma and r['own_in_best_tie_set'] for r in noisy),'maximum_true_rank':max(r['own_rank'] for r in noisy if r['sigma_radius_fraction']==sigma)} for sigma in [.001,.01]}
    report={'plan_sha256':sha(HERE/'matching-plan-frozen.json'),'target_geometry_loaded':False,'target_scores_computed':False,'null_reference_queries_computed':0,'synthetic_math_cases':len(math_rows),'synthetic_math_registration_comparisons':sum(r['registration_scores'] for r in math_rows),'exact_plants':len(exact),'exact_full_library_svd_registration_comparisons':88*88*120*2,'all_exact_true_candidates_in_tie_set':all(r['own_in_tie_set'] for r in exact),'maximum_svd_score_delta':maxdelta,'noisy_summary':summary,'noisy_plants':len(noisy),'benchmark':{'full_library_queries':176,'registrations_per_query':21120,'mean_seconds':float(np.mean(timing)),'maximum_seconds':max(timing),'projected8190_reference_queries_at_mean_seconds':float(np.mean(timing))*8190,'projection_limit':'Synthetic known-pattern timings only, not a measured reference or target runtime.'},'elapsed_seconds':time.perf_counter()-started,'math_rows':math_rows,'exact_rows':exact,'noisy_rows':noisy}
    write(HERE/'pretarget-gate.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['math_rows','exact_rows','noisy_rows']},indent=2))
if __name__=='__main__':main()
