"""Frozen full-shape synthetic power/reference study; no manuscript scoring."""
import json,time,hashlib,random
from pathlib import Path
import numpy as np
import engine,provenance,calibration
H=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_bytes())
def split(a,lengths):return list(np.split(a,np.cumsum(lengths)[:-1]))
def evaluate(a,lengths):
    context=engine.score(split(a,lengths));comp=engine.compression(a);prov=provenance.score_provenance(a)
    values=context['bits_per_rune']+[comp[n]['bits_per_rune'] for n in ('raw1','packed')]+[prov[n] for n in provenance.METRICS]
    return dict(values=values,context=context,compression=comp,provenance=prov,stream_sha256=hashlib.sha256(a.tobytes()).hexdigest(),adjacent_repeats=int(np.count_nonzero(a[1:]==a[:-1])))
def plant(kind,length,seed,lengths=None):
    rng=random.Random(seed);out=[]
    if kind=='balanced-bags':
        while len(out)<length:
            bag=list(range(29));rng.shuffle(bag);out.extend(bag)
        return np.asarray(out[:length],np.uint8)
    if kind=='frequency-drift':
        # Both halves use uniform14-symbol support, with disjoint supports; no language model.
        return np.asarray([rng.randrange(14)+(0 if i<length//2 else 15) for i in range(length)],np.uint8)
    if kind=='order1':
        for _ in range(length):
            if not out:x=rng.randrange(29)
            else:x=out[-1] if rng.randrange(29)==0 else (out[-1]+1)%29
            if out and x==out[-1] and rng.random()<.83:x=rng.randrange(29)
            out.append(x)
    elif kind=='order2':
        for i in range(length):
            x=rng.randrange(29) if i<2 or rng.random()<.1 else (out[-2]+out[-1]+1)%29
            if out and x==out[-1] and rng.random()<.83:x=rng.randrange(29)
            out.append(x)
    elif kind=='permuted-order2':
        values=plant('order2',length,seed).tolist();rng.shuffle(values)
        for x in values:
            if out and x==out[-1] and rng.random()<.83:x=rng.randrange(29)
            out.append(x)
    elif kind=='fold-mismatch':
        assert lengths is not None
        for j,size in enumerate(lengths):
            page=[];step=1 if j%2==0 else 2
            for i in range(size):
                x=rng.randrange(29) if i==0 else page[-1] if rng.randrange(29)==0 else (page[-1]+step)%29
                if page and x==page[-1] and rng.random()<.83:x=rng.randrange(29)
                page.append(x)
            out.extend(page)
    else:raise ValueError('Unknown synthetic plant')
    return np.asarray(out,np.uint8)
def main():
    p=read(H/'controls-plan-frozen.json')
    for f,h in p['pins'].items():assert hashlib.sha256((H/f).read_bytes()).hexdigest()==h
    start=time.perf_counter();lengths=p['lengths'];total=sum(lengths);names=[f'kt{k}' for k in range(1,9)]+[f'ppm{k}' for k in range(1,9)]+['lzma_raw1','lzma_packed']+list(provenance.METRICS);tails=['lower']*18+list(provenance.TAILS)
    refs=[]
    for j in range(p['reference_count']):
        seed=p['reference_seed_start']+j;r=evaluate(engine.filtered(total,seed),lengths);refs.append(dict(seed=seed,**r))
        if (j+1)%50==0:print('Synthetic references',j+1,'elapsed',time.perf_counter()-start,flush=True)
    reference=np.asarray([r['values'] for r in refs]);negative=[]
    for j in range(p['validation_count']):
        seed=p['validation_seed_start']+j;r=evaluate(engine.filtered(total,seed),lengths);negative.append(dict(seed=seed,comparison=calibration.compare(reference,r['values'],tails),**r))
    positive=[]
    for kind in p['plant_kinds']:
        for seed in p['plant_seeds']:
            r=evaluate(plant(kind,total,seed,lengths),lengths);positive.append(dict(kind=kind,seed=seed,comparison=calibration.compare(reference,r['values'],tails),**r))
    result=dict(stage='Synthetic only; manuscript rune values never loaded',plan_sha256=hashlib.sha256((H/'controls-plan-frozen.json').read_bytes()).hexdigest(),names=names,tails=tails,reference=refs,negative_validation=negative,positive=positive,negative_family_gate_passes=sum(r['comparison']['gate'] for r in negative),negative_count=len(negative),plant_family_passes={k:sum(r['comparison']['gate'] for r in positive if r['kind']==k) for k in p['plant_kinds']},seconds=time.perf_counter()-start,limits='Synthetic plants are selected capacities, not all alternatives. Shared reference bank makes validation decisions dependent. Per-model failures retained; power at one order does not validate every order. No manuscript score or family exclusion.')
    target=H/'controls-results.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print('Completed synthetic controls',result['negative_family_gate_passes'],result['plant_family_passes'],result['seconds'],flush=True)
if __name__=='__main__':main()
