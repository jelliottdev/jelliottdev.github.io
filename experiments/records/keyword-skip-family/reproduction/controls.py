"""Keyword source-chain recovery controls and synthetic-only complete-scope benchmark."""
import hashlib,json,time
from pathlib import Path
import numpy as np
import engine as e
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def readings():
    rows=read(H/'known-readings.json')['controls'];return {r['id']:sum([x['rune_indices'] for x in r['decoded_pages']],[]) for r in rows if r['id'] in ('warning','lp2-56')}
def one_plain(plain,kw,sign,atbash,phase,seed):
    need=len(plain)*4+64;key=e.env['tile_key'](kw,need)
    c,skips,used=e.encrypt(plain,key[phase:].tolist(),sign=sign,supp=.83,seed=seed)
    actual=np.asarray(c,np.int64)
    if atbash:actual=28-actual
    return actual,skips,used
def chain(actual,label,key,sign,atbash,truth=None):
    captures=[]
    def beam(ct,K,s,o,length,width):
        if width==500:
            paths,scores,ptr,latin=e.beam(ct,K,s,o,length,width,True);out=paths[0].astype(np.int64).tolist();norm=[e.Q.score_norm(e.text(p)) for p in paths];j=int(np.argmax(norm));same=np.all(paths==np.asarray(truth,np.int16),axis=1) if truth is not None and paths.shape[1]==len(truth) else np.zeros(len(paths),bool)
            detail=dict(terminal_count=len(paths),best_normalized_terminal_score=norm[j],best_normalized_terminal=paths[j].astype(np.int64).tolist(),truth_in_terminal=bool(same.any()),truth_first_cumulative_rank=int(np.flatnonzero(same)[0])+1 if same.any() else None)
        else:out=e.beam(ct,K,s,o,length,width);detail={}
        captures.append(dict(offset=int(o),length=length,width=width,plain=out,score=e.Q.score_norm(e.text(out)),**detail));return out
    e.env['beam']=beam
    hits,best=e.env['attack_page_keyword_fast'](actual,[(label,key)],sign_list=(sign,),atbash_list=(bool(atbash),))
    screen=[x for x in captures if x['width']==300];full=[x for x in captures if x['width']==500]
    row=dict(best_screen=best,phase_scores=[x['score'] for x in screen],full=full,hits=len(hits),screen_gate=best[0]>-6,full_gate=bool(hits))
    if truth is not None:row.update(exact_recovery=bool(full and full[0]['plain']==truth),recovery_fraction=sum(a==b for a,b in zip(full[0]['plain'],truth))/len(truth) if full else None)
    return row
def main():
    plan=read(H/'controls-plan-frozen.json')
    for p,h in plan['pins'].items():assert sha(H/p)==h,p
    t=time.perf_counter();kw=e.words();r=readings();e.env['beam']=e.native
    source_ok,source=e.env['gate'](verbose=False)
    # Compile and benchmark only predetermined synthetic random ciphertext.
    rng=np.random.default_rng(plan['benchmark_seed']);bench=[]
    for length,width,word in [(90,300,'TH'),(90,300,'DIVINITY'),(90,300,'CIRCUMFERENCE'),(90,300,'CICADATHREETHREEOHONE'),(277,500,'DIVINITY')]:
        ct=rng.integers(0,29,length,dtype=np.int64);key=e.env['tile_key'](e.encode(word),length*4+64);e.beam(ct,key,-1,0,length,width)
        start=time.perf_counter()
        for _ in range(plan['benchmark_repetitions']):out=e.beam(ct,key,-1,0,length,width);e.Q.score_norm(e.text(out))
        bench.append(dict(length=length,width=width,keyword=word,seconds_per_call=(time.perf_counter()-start)/plan['benchmark_repetitions']))
    rows=[];seen=set();domain=[]
    for label,key in kw:
        if tuple(key) in seen:continue
        seen.add(tuple(key));domain.append((label,key))
    for i,(label,key) in enumerate(domain):
        reading='warning' if i%2==0 else 'lp2-56';plain=r[reading];sign=-1 if i%2==0 else 1;atbash=(i//2)%2;phase=i%len(key);seed=plan['domain_seed_start']+i
        ct,skips,used=one_plain(plain,key,sign,atbash,phase,seed);result=chain(ct,label,key,sign,atbash,plain)
        rows.append(dict(group='domain',keyword=label,key=key,reading=reading,sign=sign,atbash=atbash,phase=phase,seed=seed,skips=skips,used=used,truth_encoder_path_max3=max(skips[1:],default=0)<=3,**result))
        if (i+1)%100==0:print('Own-key controls',i+1,'/617 elapsed',round(time.perf_counter()-t,3),flush=True)
    # Transformed endpoints for three source/known keywords; duplicate constant phases retained.
    for reading,plain in r.items():
        for label in plan['endpoint_keywords']:
            key=e.encode(label)
            for sign in (-1,1):
                for atbash in (0,1):
                    for phase in (0,len(key)-1):
                        seed=plan['endpoint_seed_start']+len(rows);ct,skips,used=one_plain(plain,key,sign,atbash,phase,seed);result=chain(ct,label,key,sign,atbash,plain)
                        rows.append(dict(group='endpoints',keyword=label,key=key,reading=reading,sign=sign,atbash=atbash,phase=phase,seed=seed,skips=skips,used=used,truth_encoder_path_max3=max(skips[1:],default=0)<=3,**result))
    # Four complete source-list selection searches: no own-key-only rescue of full-grid claims.
    grids=[]
    for reading,plain in r.items():
        for label in ('DIVINITY','CIRCUMFERENCE'):
            key=e.encode(label);seed=plan['full_grid_seed_start']+len(grids);ct,skips,used=one_plain(plain,key,-1,0,0,seed);calls=[0];full=[]
            def capture(c,K,s,o,length,width):
                out=e.beam(c,K,s,o,length,width);calls[0]+=int(width==300)
                if width==500:full.append(dict(sign=s,offset=int(o),length=length,plain=out,score=e.Q.score_norm(e.text(out)),exact=out==plain))
                return out
            e.env['beam']=capture;start=time.perf_counter();hits,best=e.env['attack_page_keyword_fast'](ct,kw)
            grids.append(dict(reading=reading,true_keyword=label,seed=seed,screens=calls[0],full_outputs=full,hits=len(hits),best_screen=best,exact_output_found=any(x['exact'] for x in full),exact_gate_hit=any(x['exact'] and x['score']> -5.5 for x in full),seconds=time.perf_counter()-start));print('Full synthetic keyword grid',reading,label,calls[0],round(grids[-1]['seconds'],3),'seconds',flush=True)
    result=dict(stage='Synthetic controls only; no manuscript values loaded or scored',plan_sha256=sha(H/'controls-plan-frozen.json'),source_gate_pass=source_ok,source_gate=source,benchmarks=bench,projected_target_screen_seconds=619080*max(x['seconds_per_call'] for x in bench if x['width']==300),domain_count=len(domain),controls=rows,full_grids=grids,domain_screen_passes=sum(x['screen_gate'] for x in rows if x['group']=='domain'),domain_full_passes=sum(x['full_gate'] for x in rows if x['group']=='domain'),domain_exact_recoveries=sum(x['exact_recovery'] for x in rows if x['group']=='domain'),seconds=time.perf_counter()-t,limits='Source-gate passage is not complete recovery. Domain trials reuse2known passages and do not validate all per-key transforms. Unbounded encoder rejection differs from decoder max3. Every failed chain/output retained; no missing control is replaced.')
    out=H/'controls-results.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('Synthetic controls done',result['domain_screen_passes'],result['domain_full_passes'],result['domain_exact_recoveries'],'of617',round(result['seconds'],3),'seconds',flush=True)
if __name__=='__main__':main()
