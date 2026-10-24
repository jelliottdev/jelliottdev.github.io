"""Entire fixed-primer domain on known readings, with exact source encoder retained."""
import hashlib,json,random,time
from pathlib import Path
import numpy as np
import engine as e
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def true_feasible(ct,plain,primer,mode,sign):
    # Independent of beam ranking: enumerate every pointer able to yield the fixed truth.
    lp=len(primer);L=len(ct);need=max(lp+L,4*L+8)
    def key(t,known):
        if t<lp:return primer[t]
        u=t-lp
        if mode=='P':return plain[u] if u<known else None
        return ct[u] if u<L else 0
    if (ct[0]+sign*primer[0])%29!=plain[0]:return False,0
    pointers={0};maximum=1
    for i in range(1,L):
        nxt=set()
        for pa in pointers:
            for skip in range(4):
                acc=pa+1+skip
                if mode=='C' and acc>=need:break
                k=key(acc,i)
                if k is None:break
                if (ct[i]+sign*k)%29!=plain[i]:continue
                if all(key(t,i) is not None and (plain[i]-sign*key(t,i))%29==ct[i-1] for t in range(pa+1,acc)):nxt.add(acc)
        pointers=nxt;maximum=max(maximum,len(pointers))
        if not pointers:return False,maximum
    return True,maximum
def main():
    plan=json.loads((H/'controls-plan-frozen.json').read_bytes())
    for p,h in plan['pins'].items():assert sha(H/p)==h,p
    started=time.perf_counter();known=json.loads((H/'known-readings.json').read_bytes())
    texts={x['id']:sum([p['rune_indices'] for p in x['decoded_pages']],[]) for x in known['controls'] if x['id'] in ('warning','lp2-56')}
    source_gate=e.env['gate'](verbose=False);rows=[];wp=e.encode('MABINOGION')
    for j,(label,primer) in enumerate(e.primers()):
        for mode in ('P','C'):
            for sign in (-1,1):
                for reading in ('warning','lp2-56'):
                    seed=plan['seed_start']+len(rows);plain=texts[reading];ct,skips,used=e.encrypt(plain,primer,sign=sign,supp=.83,seed=seed,mode=mode)
                    paths,cum,ptr,latin=e.terminals(ct,primer,sign,450,mode);norm=np.asarray([e.Q.score_norm(e.text(p)) for p in paths]);best=int(np.argmax(norm));same=np.all(paths==np.asarray(plain),axis=1);truthrank=int(np.flatnonzero(same)[0])+1 if same.any() else None
                    valid,pointer_states=true_feasible(ct,plain,primer,mode,sign);wrong=e.decode(ct,wp,sign,450,mode)
                    rows.append(dict(case=len(rows),primer_label=label,primer_index=j,primer=primer,mode=mode,sign=sign,reading=reading,seed=seed,ciphertext=ct,skips=skips,key_used_len=used,encoder_path_max3=max(skips[1:],default=0)<=3,truth_feasible=valid,truth_pointer_max_states=pointer_states,output=paths[0].tolist(),score=float(norm[0]),cumulative=float(cum[0]),pointer=int(ptr[0]),output_length=paths.shape[1],exact_recovery=bool(same[0]),fraction=sum(int(a)==b for a,b in zip(paths[0],plain))/len(plain),source_gate=bool(norm[0]>-5.5),truth_in_terminal=bool(same.any()),truth_first_cumulative_rank=truthrank,terminal_count=len(paths),best_normalized_score=float(norm[best]),best_normalized_rank=best+1,best_normalized_output=paths[best].tolist(),wrong_primer_score=wrong['score'],wrong_primer_output=wrong['plain_idx'],wrong_primer_gate=wrong['score']> -5.5))
        if (j+1)%5==0:print('Synthetic primer labels',j+1,'/45 controls',len(rows),'elapsed',round(time.perf_counter()-started,3),flush=True)
    benchmarks=[]
    for L in plan['benchmark_lengths']:
        for word in plan['benchmark_primers']:
            rng=random.Random(plan['benchmark_seed']+L+len(word));ct=[rng.randrange(29) for _ in range(L)];primer=e.encode(word)
            for mode in ('P','C'):
                e.decode(ct,primer,-1,450,mode);t=time.perf_counter()
                for _ in range(plan['benchmark_repetitions']):e.decode(ct,primer,-1,450,mode)
                benchmarks.append(dict(length=L,primer=word,mode=mode,seconds_per_call=(time.perf_counter()-t)/plan['benchmark_repetitions']))
    summary={mode:dict(total=sum(x['mode']==mode for x in rows),exact=sum(x['mode']==mode and x['exact_recovery'] for x in rows),score_pass=sum(x['mode']==mode and x['source_gate'] for x in rows),truth_feasible=sum(x['mode']==mode and x['truth_feasible'] for x in rows),truth_terminal=sum(x['mode']==mode and x['truth_in_terminal'] for x in rows),wrong_score_pass=sum(x['mode']==mode and x['wrong_primer_gate'] for x in rows)) for mode in ('P','C')}
    result=dict(stage='Synthetic only; no manuscript loaded or scored',plan_sha256=sha(H/'controls-plan-frozen.json'),original_gate=source_gate,domain=rows,summary=summary,benchmarks=benchmarks,projected_target_seconds=9900*max(x['seconds_per_call'] for x in benchmarks),seconds=time.perf_counter()-started,limits='Two independent known passages are reused. Exact recovery, source score passage, truth admissibility and ranking are separate. Source encoder/decoder frontier asymmetries are retained, not repaired. No target/family exclusion authorized by these controls.')
    out=H/'controls-results.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('CONTROLS DONE',summary,'projection',result['projected_target_seconds'],flush=True)
if __name__=='__main__':main()
