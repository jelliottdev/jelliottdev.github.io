"""Full shifted manuscript English grid using the exact prior Numba scorer."""
import argparse,ast,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from numba import njit
HERE=Path(__file__).resolve().parent
SPACE=26**4
def source_function(filename,function):
    tree=ast.parse((HERE/'source'/filename).read_text(encoding='utf-8'));tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function]
    ns={'np':np,'njit':njit,'SPACE':SPACE,'MOD':SPACE};exec(compile(tree,filename,'exec'),ns);return ns[function]
score_pair=source_function('prior_run.py','score_pair')
@njit
def shifted_grid(pages,lengths,symbols,sizes,freq,retain):
    count=0
    for i in range(len(lengths)):
        for j in range(i+1,len(lengths)):
            if min(lengths[i],lengths[j])>=120:count+=lengths[i]+lengths[j]-239
    scores_out=np.empty((count if retain else 0,3),np.float64);groups_out=np.empty((count if retain else 0,3),np.int64);cases=np.empty((count if retain else 0,4),np.int64)
    row=0;best=-1e300;bestrow=np.zeros(7,np.int64);clears=0
    for i in range(len(lengths)):
        for j in range(i+1,len(lengths)):
            na,nb=lengths[i],lengths[j]
            if min(na,nb)<120:continue
            for lag in range(-(nb-120),na-120+1):
                sa=max(lag,0);sb=max(-lag,0);n=min(na-sa,nb-sb)
                scores,groups=score_pair(pages[i,sa:sa+n],pages[j,sb:sb+n],symbols,sizes,freq)
                for arm in range(3):
                    if scores[arm]>=-5.5:clears+=1
                    if scores[arm]>best:
                        best=scores[arm];bestrow=np.array([i,j,lag,n,arm,groups[arm],row],np.int64)
                if retain:
                    scores_out[row]=scores;groups_out[row]=groups;cases[row]=np.array([i,j,lag,n],np.int64)
                row+=1
    return best,bestrow,clears,scores_out,groups_out,cases
def setup():
    raw=(HERE/'frozen-plan.json').read_bytes();plan=json.loads(raw)
    for x in plan['inputs']:assert hashlib.sha256((HERE/x['path']).read_bytes()).hexdigest()==x['sha256']
    labels=json.loads((HERE/'labels.json').read_text(encoding='utf-8'));symbols=np.zeros((29,2),np.int64);sizes=np.array(list(map(len,labels)),np.int64)
    for i,label in enumerate(labels):
        for j,c in enumerate(label):symbols[i,j]=ord(c)-65
    counts={g:int(c) for g,c in [line.split() for line in (HERE/'english_quadgrams.txt').read_text(encoding='ascii').splitlines()]};norm=math.log10(sum(counts.values()));freq=np.full(SPACE,math.log10(.01)-norm,np.float64)
    for gram,num in counts.items():
        slot=0
        for c in gram:slot=26*slot+ord(c)-65
        freq[slot]=math.log10(num)-norm
    pagejson=json.loads((HERE/'pages.json').read_text(encoding='utf-8'));streams=[x['runes'] for x in pagejson];lengths=np.array(list(map(len,streams)),np.int64);pages=np.zeros((55,int(lengths.max())),np.int64)
    for i,s in enumerate(streams):pages[i,:len(s)]=s
    return plan,raw,[x['id'] for x in pagejson],pages,lengths,symbols,sizes,freq,labels
def outcome(score,row,clears):
    return {'score':float(score),'i':int(row[0]),'j':int(row[1]),'lag':int(row[2]),'overlap':int(row[3]),'arm':int(row[4]),'quadgrams':int(row[5]),'row':int(row[6]),'streams_at_or_above_minus5_5':int(clears)}
def controls(plan,symbols,sizes,freq):
    P=json.loads((HERE/'warning.json').read_text(encoding='utf-8'))['rune_indices'];rng=np.random.default_rng(plan['positive_controls']['random_key_seed']);rows=[]
    for arm,lag in enumerate(plan['positive_controls']['operation_lags']):
        sa=max(lag,0);sb=max(-lag,0);a=rng.integers(0,29,len(P)+sa,dtype=np.int64);b=rng.integers(0,29,len(P)+sb,dtype=np.int64)
        for t,p in enumerate(P):b[sb+t]=(p-a[sa+t])%29 if arm==0 else (a[sa+t]-p)%29 if arm==1 else (p+a[sa+t])%29
        lengths=np.array([len(a),len(b)],np.int64);pages=np.zeros((2,int(lengths.max())),np.int64);pages[0,:len(a)]=a;pages[1,:len(b)]=b
        score,row,clears,*_=shifted_grid(pages,lengths,symbols,sizes,freq,False)
        assert row[2]==lag and row[4]==arm and score>-5.5
        wrong=b.copy();rng.shuffle(wrong);pages[1,:len(b)]=wrong;ws,wr,wc,*_=shifted_grid(pages,lengths,symbols,sizes,freq,False);assert ws<-5.5
        rows.append({'operation':plan['operations'][arm],'arm':arm,'lag':lag,'a':a.tolist(),'b':b.tolist(),'reading':P,'best':outcome(score,row,clears),'shuffled_b':wrong.tolist(),'shuffled_best':outcome(ws,wr,wc)})
    return rows
def generate():
    plan,raw,ids,pages,lengths,symbols,sizes,freq,labels=setup();plants=controls(plan,symbols,sizes,freq)
    score,row,clears,scores,groups,cases=shifted_grid(pages,lengths,symbols,sizes,freq,True);assert len(cases)==331908
    best=outcome(score,row,clears);i,j,lag,n,arm=map(int,row[:5]);sa=max(lag,0);sb=max(-lag,0);a=pages[i,sa:sa+n];b=pages[j,sb:sb+n];values=(a+b)%29 if arm==0 else (a-b)%29 if arm==1 else (b-a)%29;best['rune_indices']=values.tolist();best['latin']=''.join(labels[int(x)] for x in values)
    rng=np.random.default_rng(plan['null_seed']);nulls=[]
    for t in range(plan['null_trials']):
        shuffled=pages.copy()
        for p,nv in enumerate(lengths):shuffled[p,:nv]=rng.permutation(pages[p,:nv])
        s,w,c,*_=shifted_grid(shuffled,lengths,symbols,sizes,freq,False);nulls.append(outcome(s,w,c))
        if (t+1)%16==0:print(f'English null grids {t+1}/{plan["null_trials"]}',flush=True)
    exceed=sum(v['score']>=score for v in nulls)
    result={'schema':'shifted-page-pair-english-v1','plan_sha256':hashlib.sha256(raw).hexdigest(),'page_ids':ids,'alignment_count':len(cases),'stream_count':int(scores.size),'eligible_streams':int((groups>=100).sum()),'new_nonzero_lag_streams':int((cases[:,2]!=0).sum())*3,'observed':best,'positive_controls':plants,'null_maxima':nulls,'null_at_or_above_observed':exceed,'global_empirical_plus_one':(exceed+1)/(len(nulls)+1),'score_array_sha256':hashlib.sha256(scores.astype('<f8').tobytes()).hexdigest(),'quadgram_array_sha256':hashlib.sha256(groups.astype('<i8').tobytes()).hexdigest(),'case_array_sha256':hashlib.sha256(cases.astype('<i8').tobytes()).hexdigest()}
    return result,scores,groups,cases
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r,s,g,c=generate()
    if args.check:
        old=json.loads((HERE/'results.json').read_text(encoding='utf-8'));assert r==old
        archive=np.load(HERE/'cases.npz');assert np.array_equal(s,archive['scores']) and np.array_equal(g,archive['quadgrams']) and np.array_equal(c,archive['cases']);print('PASS: complete observed and128-null English grid')
    else:
        (HERE/'results.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');np.savez_compressed(HERE/'cases.npz',scores=s,quadgrams=g,cases=c);print(json.dumps({k:r[k] for k in ['stream_count','observed','null_at_or_above_observed','global_empirical_plus_one']}))
