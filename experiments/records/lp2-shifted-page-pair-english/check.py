"""Separate prior one-stream scorer and independent shifted enumeration."""
import ast,hashlib,json,math
from pathlib import Path
import numpy as np
from numba import njit
HERE=Path(__file__).resolve().parent;MOD=26**4
tree=ast.parse((HERE/'source/prior_check.py').read_text(encoding='utf-8'));tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='one_stream'];ns={'njit':njit,'np':np,'MOD':MOD};exec(compile(tree,'prior_check.py','exec'),ns);one_stream=ns['one_stream']
@njit
def independent_grid(pages,lengths,letters,sizes,table):
    N=0
    for i in range(len(lengths)):
        for j in range(i+1,len(lengths)):
            if min(lengths[i],lengths[j])>=120:N+=lengths[i]+lengths[j]-239
    scores=np.empty((N,3),np.float64);quads=np.empty((N,3),np.int64);cases=np.empty((N,4),np.int64);r=0
    for i in range(len(lengths)):
        for j in range(i+1,len(lengths)):
            if min(lengths[i],lengths[j])<120:continue
            for displacement in range(120-lengths[j],lengths[i]-119):
                x=max(displacement,0);y=max(-displacement,0);n=min(lengths[i]-x,lengths[j]-y)
                for direction in range(3):scores[r,direction],quads[r,direction]=one_stream(pages[i,x:x+n],pages[j,y:y+n],direction,letters,sizes,table)
                cases[r]=np.array([i,j,displacement,n]);r+=1
    return scores,quads,cases
def main():
    p=json.loads((HERE/'frozen-plan.json').read_text(encoding='utf-8'));r=json.loads((HERE/'results.json').read_text(encoding='utf-8'));saved=np.load(HERE/'cases.npz')
    assert hashlib.sha256((HERE/'frozen-plan.json').read_bytes()).hexdigest()==r['plan_sha256']
    for item in p['inputs']:assert hashlib.sha256((HERE/item['path']).read_bytes()).hexdigest()==item['sha256']
    labels=json.loads((HERE/'labels.json').read_text(encoding='utf-8'));letters=np.zeros((29,2),np.int64);sizes=np.array(list(map(len,labels)),np.int64)
    for i,label in enumerate(labels):
        for j,c in enumerate(label):letters[i,j]=ord(c)-65
    countrows=[line.split() for line in (HERE/'english_quadgrams.txt').read_text(encoding='ascii').splitlines()];total=sum(int(x[1]) for x in countrows);normalizer=math.log10(total);table=np.full(MOD,math.log10(.01)-normalizer)
    for gram,count in countrows:
        idx=sum((ord(c)-65)*26**(3-i) for i,c in enumerate(gram));table[idx]=math.log10(int(count))-normalizer
    pagejson=json.loads((HERE/'pages.json').read_text(encoding='utf-8'));streams=[x['runes'] for x in pagejson];lengths=np.array(list(map(len,streams)),np.int64);pages=np.zeros((len(streams),max(lengths)),np.int64)
    for i,s in enumerate(streams):pages[i,:len(s)]=s
    scores,quads,cases=independent_grid(pages,lengths,letters,sizes,table)
    delta=float(np.max(np.abs(scores-saved['scores'])));assert delta<=2e-12
    assert np.array_equal(quads,saved['quadgrams']) and np.array_equal(cases,saved['cases'])
    assert scores.size==995724 and int((cases[:,2]!=0).sum())*3==991746 and (quads>=100).all()
    ix=int(scores.argmax());row,arm=divmod(ix,3);best=r['observed'];assert cases[row].tolist()==[best['i'],best['j'],best['lag'],best['overlap']] and arm==best['arm'] and abs(scores[row,arm]-best['score'])<2e-12
    assert int((scores>=-5.5).sum())==best['streams_at_or_above_minus5_5']
    for ctrl in r['positive_controls']:
        a,b=ctrl['a'],ctrl['b'];lag=ctrl['lag'];x=max(lag,0);y=max(-lag,0);P=ctrl['reading'];arm=ctrl['arm'];recovered=[]
        for va,vb in zip(a[x:x+184],b[y:y+184]):recovered.append((va+vb)%29 if arm==0 else (va-vb)%29 if arm==1 else (vb-va)%29)
        assert recovered==P
        value,n=one_stream(np.array(a[x:]),np.array(b[y:]),arm,letters,sizes,table);assert value>-5.5 and abs(value-ctrl['best']['score'])<2e-12
        control_lengths=np.array([len(a),len(b)],np.int64);control_pages=np.zeros((2,int(control_lengths.max())),np.int64);control_pages[0,:len(a)]=a;control_pages[1,:len(b)]=b
        cs,cq,cc=independent_grid(control_pages,control_lengths,letters,sizes,table);at=int(cs.argmax());cr,ca=divmod(at,3)
        assert int(cc[cr,2])==lag and ca==arm and abs(float(cs[cr,ca])-ctrl['best']['score'])<2e-12
        control_pages[1,:len(b)]=ctrl['shuffled_b'];ws,wq,wc=independent_grid(control_pages,control_lengths,letters,sizes,table)
        assert float(ws.max())<-5.5 and abs(float(ws.max())-ctrl['shuffled_best']['score'])<2e-12
    rng=np.random.default_rng(p['null_seed'])
    for winner in r['null_maxima']:
        shuffled=[rng.permutation(np.array(s,dtype=np.int64)) for s in streams];lag=winner['lag'];n=winner['overlap'];x=max(lag,0);y=max(-lag,0)
        value,count=one_stream(shuffled[winner['i']][x:x+n],shuffled[winner['j']][y:y+n],winner['arm'],letters,sizes,table)
        assert abs(value-winner['score'])<2e-12 and count==winner['quadgrams']
    exceed=sum(x['score']>=best['score'] for x in r['null_maxima']);assert exceed==r['null_at_or_above_observed'] and (exceed+1)/129==r['global_empirical_plus_one']
    # Exact zero-offset subset is shared with the published English baseline.
    prior=HERE.parent/'lp2-page-pair-english/results.json'
    if prior.exists():
        old=json.loads(prior.read_text(encoding='utf-8'));lookup={(x['page_a'],x['page_b'],x['operation']):x for x in old['observed_cases']};zero=np.where(cases[:,2]==0)[0]
        for at in zero:
            i,j,_,n=cases[at]
            for arm,op in enumerate(p['operations']):assert abs(scores[at,arm]-lookup[(r['page_ids'][i],r['page_ids'][j],op)]['score'])<2e-12
        assert len(zero)*3==3978
    print(f'PASS: all995724 independent English scores; max delta={delta:.3g};3978 baseline overlaps; exact Warning plants;128 null winners; global comparison')
if __name__=='__main__':main()
