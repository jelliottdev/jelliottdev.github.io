"""Portable independent full observed-score and bounded null audit. No producer imports."""
import sys,argparse,json,hashlib,random,io,time
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
import independent as I
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def array_sha(a):
    stream=io.BytesIO();np.save(stream,a,allow_pickle=False);return hashlib.sha256(stream.getvalue()).hexdigest()
def corpus(pages,seed):
    rng=random.Random(seed);out=[]
    for row in pages:
        c=list(row['runes']);rng.shuffle(c);out.append(c)
    return out

def audit(root,prior=None):
    started=time.perf_counter();audit_plan=read(HERE/'audit-plan-frozen.json')
    for item in audit_plan['files']:assert sha(HERE/item['path'])==item['sha256']
    p=read(root/'protocol-frozen.json');pages=read(root/'pages.json')['pages'];labels=p['labels'];effective=p['effective_labels']
    for row in p['files']:assert sha(root/row['path'])==row['sha256'],row['path']
    for row in read(root/'source-manifest.json')['files']:assert sha(root/row['path'])==row['sha256'],row['path']
    assert len(labels)==56 and len(effective)==48 and len(pages)==55
    assert p['null_seed']==3301241024 and p['null_replicates']==49
    assert sum(len(row['runes']) for row in pages)==12956
    for row in pages:assert hashlib.sha256(bytes(row['runes'])).hexdigest()==row['runes_sha256']
    model=I.setup(root/'source');base,primes,letters,table=model
    gp_labels=[''.join(chr(int(x)+65) for x in row if x>=0) for row in letters]
    result=read(root/'results.json');observed=read(root/'observed-witnesses.json')
    for field,name in [('protocol_sha256','protocol-frozen.json'),('observed_effective_scores_sha256','observed-effective-scores.npy'),('null_page_scores_sha256','null-page-maxima-scores.npy'),('null_page_primers_sha256','null-page-maxima-primers.npy')]:assert result[field]==sha(root/name),name
    saved=np.load(root/'observed-effective-scores.npy',allow_pickle=False);assert saved.shape==(48,55,841)
    scores=np.empty_like(saved);checked=0;maxerror=0.
    for ei,label in enumerate(effective):
        for pi,page in enumerate(pages):
            ct=np.array(page['runes'][::-1] if label['direction']=='reverse' else page['runes'],dtype=np.int64)
            values=I.grid(ct,I.NAMES.index(label['function']),int(label['history']=='mix'),label['sign'],*model)
            error=float(np.max(np.abs(values-saved[ei,pi])));assert error<1e-12,(ei,pi,error)
            maxerror=max(maxerror,error);scores[ei,pi]=values;checked+=841
    print('Independent observed scores checked:',checked,'maximum error',maxerror,flush=True)
    index={row['id']:i for i,row in enumerate(effective)};neg=np.array([(-a)%29*29+(-b)%29 for a in range(29) for b in range(29)])
    full=np.empty((56,55,841),dtype=np.float64)
    for li,label in enumerate(labels):
        values=scores[index[label['representative']]]
        full[li]=values[:,neg] if label['negate_starting_key'] else values
    assert full.size==p['labelled_target_cases']==2590280 and scores.size==p['effective_target_cases']==2220240
    witness_count=0
    def witness(w,ciphers,expected=None):
        nonlocal witness_count
        li=next(i for i,l in enumerate(labels) if l['id']==w['label']);label=labels[li];pi=next(i for i,row in enumerate(pages) if row['page']==w['page']);a,b=w['starting_key'];ordinal=a*29+b
        if expected is not None:assert (li,pi,ordinal)==expected,('selection',expected,(li,pi,ordinal))
        C=ciphers[pi][::-1] if label['direction']=='reverse' else ciphers[pi]
        P=I.decode(np.array(C,dtype=np.int64),a,b,I.NAMES.index(label['function']),int(label['history']=='mix'),label['sign'],base,primes)
        assert P.tolist()==w['runes'] and hashlib.sha256(bytes(P.tolist())).hexdigest()==w['decoded_sha256']
        text=''.join(gp_labels[i] for i in P);tail=''.join(gp_labels[i] for i in P[2:])
        assert text==w['transliteration'] and tail==w['scored_tail'] and len(tail)-3==w['quadgrams']
        assert abs(I.score(P,letters,table)-w['score'])<1e-12
        assert all(w[k]==label[k] for k in ['function','sign','direction']) and w['history']==label['history'];witness_count+=1
    original=[row['runes'] for row in pages]
    maxima=np.max(full,axis=2);primers=np.argmax(full,axis=2)
    li,pi=np.unravel_index(int(np.argmax(maxima)),maxima.shape);witness(observed['best'],original,(int(li),int(pi),int(primers[li,pi])))
    assert observed==result['observed'] and observed['effective_score_sha256']==sha(root/'observed-effective-scores.npy')
    for flat,w in zip(np.argsort(-full.reshape(-1),kind='stable')[:40],observed['top40']):
        li,rest=divmod(int(flat),55*841);pi,j=divmod(rest,841);witness(w,original,(li,pi,j))
    assert len(observed['top40'])==40 and len(observed['per_label_best'])==56
    for li,w in enumerate(observed['per_label_best']):
        pi=int(np.argmax(maxima[li]));witness(w,original,(li,pi,int(primers[li,pi])))
    ns=np.load(root/'null-page-maxima-scores.npy',allow_pickle=False);npair=np.load(root/'null-page-maxima-primers.npy',allow_pickle=False)
    assert ns.shape==npair.shape==(49,56,55) and np.all(npair<841)
    assert len(result['null_global_witnesses'])==49
    null_witnesses=0;sample_grids=0;global_grids=0;null_error=0.;sample_coordinates=set();prior_cells=0;prior_error=0.
    old=np.load(prior,allow_pickle=False,mmap_mode='r') if prior else None
    if old is not None:
        assert old.shape==(50,55,841)
        manifest=read(root/'prior-score-sha256.json');assert sha(prior)==manifest['source_scorefile_sha256']
        ei=next(i for i,l in enumerate(effective) if l['function']=='sum' and l['history']=='pt' and l['sign']==-1 and l['direction']=='forward')
        prior_error=float(np.max(np.abs(scores[ei]-old[0])));assert prior_error<1e-12;prior_cells+=55*841
    for ti,record in enumerate(result['null_global_witnesses']):
        trial=ti+1;seed=3301241024+ti;assert record['trial']==trial and record['seed']==seed and record['protocol_sha256']==sha(root/'protocol-frozen.json')
        shuffled=corpus(pages,seed);assert hashlib.sha256(b''.join(bytes(c) for c in shuffled)).hexdigest()==record['input_sha256']
        assert array_sha(ns[ti])==record['scores_sha256'] and array_sha(npair[ti])==record['primers_sha256']
        li,pi=np.unravel_index(int(np.argmax(ns[ti])),ns[ti].shape)
        witness(record['best'],shuffled,(int(li),int(pi),int(npair[ti,li,pi])))
        assert record['best']['score']==float(ns[ti,li,pi])
        for lj,label in enumerate(labels):
            for pj,C0 in enumerate(shuffled):
                C=C0[::-1] if label['direction']=='reverse' else C0;a,b=divmod(int(npair[ti,lj,pj]),29)
                P=I.decode(np.array(C,dtype=np.int64),a,b,I.NAMES.index(label['function']),int(label['history']=='mix'),label['sign'],base,primes)
                error=abs(I.score(P,letters,table)-ns[ti,lj,pj]);assert error<1e-12;(null_error:=max(null_error,error));null_witnesses+=1
        def check_grid(lj,pj,global_cell=False):
            nonlocal sample_grids,global_grids
            label=labels[lj];C=shuffled[pj][::-1] if label['direction']=='reverse' else shuffled[pj]
            values=I.grid(np.array(C,dtype=np.int64),I.NAMES.index(label['function']),int(label['history']=='mix'),label['sign'],*model)
            assert int(np.argmax(values))==int(npair[ti,lj,pj]) and abs(float(np.max(values))-ns[ti,lj,pj])<1e-12
            if global_cell:global_grids+=1
            else:sample_grids+=1
        check_grid(int(li),int(pi),True)
        if trial in [1,25,49]:
            for label in effective:
                lj=next(j for j,l in enumerate(labels) if l['id']==label['id'])
                for pj in [0,27,54]:check_grid(lj,pj)
        if old is not None:
            for pj,C in enumerate(shuffled):
                values=I.grid(np.array(C,dtype=np.int64),0,0,-1,*model);error=float(np.max(np.abs(values-old[trial,pj])));assert error<1e-12;prior_error=max(prior_error,error);prior_cells+=841
        if trial%10==0:print('Independent null witnesses checked through trial',trial,flush=True)
    # Alias scores are identical for every corpus; tied primers remain label-specific.
    for lj,label in enumerate(labels):
        if label['negate_starting_key']:
            canonical=next(j for j,l in enumerate(labels) if l['id']==label['representative']);assert np.array_equal(ns[:,lj],ns[:,canonical])
    maximum=float(np.max(ns));bar=max(-5.5,maximum+.5)
    assert result['null_maximum']==maximum and result['hit_bar']==bar
    assert result['null_ge_observed']==int(np.sum(np.max(ns,axis=(1,2))>=observed['best']['score']))
    coordinates=[tuple(map(int,row)) for row in np.argwhere(full>=bar)];assert len(coordinates)==len(result['gate_hits'])
    for coord,w in zip(coordinates,result['gate_hits']):witness(w,original,coord)
    assert result['labelled_cases']==2590280 and result['effective_cases']==2220240 and result['null_replicates']==49 and result['reused_prior_scores'] is False
    receipt=dict(schema='r12-c1-independent-family-audit-v1',protocol_sha256=sha(root/'protocol-frozen.json'),audit_plan_sha256=sha(HERE/'audit-plan-frozen.json'),audit_script_sha256=sha(HERE/'audit_run.py'),independent_decoder_scorer_sha256=sha(HERE/'independent.py'),results_sha256=sha(root/'results.json'),observed_effective_scores_checked=checked,observed_labelled_scores_after_exact_alias_expansion=int(full.size),observed_maximum_absolute_score_error=maxerror,observed_and_global_witnesses_checked=witness_count,null_reported_page_label_maximum_witness_scores_checked=null_witnesses,null_witness_score_maximum_error=null_error,fixed_null_full_grids_checked=sample_grids,reported_null_global_winner_full_grids_checked=global_grids,null_full_candidate_grid_audit='Sampled fixed432grids plus49reported winnergrids; other discarded null candidates not independently reconstructed.',prior_corner_candidate_scores_checked=prior_cells,prior_corner_maximum_error=prior_error,alias_scores_and_observed_stable_ties_verified=True,all49_corpus_hashes_and_compact_receipt_hashes_verified=True,global_null_aggregation_verified=True,observed_best=observed['best']['score'],null_maximum=maximum,hit_bar=bar,gate_hits=len(coordinates),null_ge_observed=result['null_ge_observed'],controls='All failed prototype identification outcomes remain a limit; this audit validates score enumeration, not family rejection or plaintext.',seconds=time.perf_counter()-started)
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run-root',required=True,type=Path);p.add_argument('--prior-scores',type=Path);p.add_argument('--output',type=Path);p.add_argument('--check-only',action='store_true');a=p.parse_args();assert a.check_only != (a.output is not None), 'Choose --output NEW_RECEIPT or --check-only';assert a.output is None or not a.output.exists()
    receipt=audit(a.run_root.resolve(),a.prior_scores.resolve() if a.prior_scores else None)
    if a.output:a.output.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
