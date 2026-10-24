"""Bounded prefix extension. Original scanner/parser bytes are never modified."""
import argparse, hashlib, json, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
import numpy as np
import portable
H = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()
def ah(a): return sha(np.asarray(a, dtype='<i2').tobytes())
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, value):
    p = Path(p)
    if p.exists(): raise ValueError('Refusing overwrite: '+str(p))
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
def patterns(sk):
    lp, fc = sk.lp2_words(); rng = np.random.default_rng(3301)
    for _ in range(4): rng.permutation(len(lp))
    out = {}
    for w in (400,120):
        out[f'realW{w}:interval'] = (lp[:w],fc[:w])
        for k in range(2):
            i = rng.permutation(w); out[f'n{k}W{w}:interval']=(lp[:w][i],fc[:w][i])
    return out
def direct(a, obs, fc):
    w=len(obs)
    if len(a)<w:return np.array([],dtype=np.int16)
    windows=np.lib.stride_tricks.sliding_window_view(a,w)
    # groups_interval ignores observed values outside 1..29; BlockCache clips 1..40.
    return ((windows>=np.maximum(1,obs-fc)) & (windows<=np.minimum(40,obs)) & (obs>=1) & (obs<=29)).sum(axis=1).astype(np.int16)
def compiled(sk, sc, pats):
    return [sc.Pattern(n,sk.groups_interval(o,f),len(o)) for n,(o,f) in pats.items()]
def load(inputs):
    if np.__version__!='2.5.4':raise ValueError('Canonical raw FFT replay requires NumPy 2.5.4')
    sk,sc,C,_=portable.validate_inputs(inputs)
    return sk,sc,C,patterns(sk)
def pin_patterns(pats):
    return {n:dict(width=len(o),observed_sha256=ah(o),fcounts_sha256=ah(f)) for n,(o,f) in pats.items()}
def controls(inputs):
    sk,sc,C,pats=load(inputs);rng=np.random.default_rng(330120261025);rows=[];start=time.perf_counter();maxerr=0.
    for n,(obs,fc) in pats.items():
        w=len(obs);cases=[]
        for label,m,off in [('first',w+37,0),('final',w+37,37),('exact',w,0),('too-short',w-1,None)]+([('short-carrier',250,71)] if w==120 else []):
            a=rng.integers(1,20,m,dtype=np.int16)
            if off is not None:a[off:off+w]=obs
            cases.append((label,a,off))
        cases.append(('random',rng.integers(0,43,w+61,dtype=np.int16),None))
        for label,a,off in cases:
            ps=compiled(sk,sc,{n:(obs,fc)});best,pt=sc.scan_corpus({'synthetic':a},ps);raw=sc.scan_block(a,ps).get(n,np.array([]));ints=direct(a,obs,fc)
            assert len(raw)==len(ints)
            err=float(np.max(np.abs(raw-ints))) if len(raw) else 0.;maxerr=max(maxerr,err);assert err<.01
            if len(raw):
                j=int(raw.argmax());assert best[n]==(float(raw[j]),'synthetic',j) and pt[n]['synthetic']==float(raw[j])
                assert ints[j]==ints.max()
                if off is not None:assert ints[off]==w
                r=dict(best_raw=float(raw[j]),selected_offset=j,integer_max=int(ints.max()),integer_tie_count=int((ints==ints.max()).sum()),truth_count=int(ints[off]) if off is not None else None)
            else:
                assert best[n]==(-1.,None,-1) and pt[n]=={};r={}
            rows.append(dict(pattern=n,case=label,words=len(a),truth_offset=off,alignments=len(ints),integer_scores_sha256=ah(ints),max_fft_error=err,**r))
    # Constant integer ties may differ slightly in FFT arithmetic; keep raw argmax.
    for w in (400,120):
        obs=np.full(w,5,np.int16);fc=np.zeros(w,np.int16);ps=compiled(sk,sc,{'tie':(obs,fc)})
        for value in (5,0):
            a=np.full(w+17,value,np.int16);best,_=sc.scan_corpus({'z':a,'a':a},ps);v=sc.scan_block(a,ps)['tie']
            assert best['tie']==(float(v.max()),'a',int(v.argmax()))
            assert np.max(np.abs(v-(w if value==5 else 0)))<.001
            if value==0:assert best['tie']==(0.,'a',0)
            rows.append(dict(pattern='tie',width=w,case='constant-two-texts',value=value,selected=best['tie'],alignments=36,raw_tie_count=int((v==v.max()).sum()),integer_tie_count=len(v)))
    result=dict(patterns=pin_patterns(pats),cases=rows,case_count=len(rows),max_fft_error=maxerr,seconds=time.perf_counter()-start,checks='Every synthetic alignment independently integer-counted; first/final/exact/too-short/random and width120 250-word carrier; raw FFT argmax and exact constant tie behavior retained. Six prefixes are deterministic dependent patterns, not six independent known texts.')
    write(H/'controls.json',result);print('Controls PASS',len(rows),'cases',result['seconds'],'seconds',flush=True)
def freeze(inputs):
    sk,sc,C,pats=load(inputs);ctrl=read(H/'controls.json');assert ctrl['patterns']==pin_patterns(pats)
    selected={str(w):[dict(name=n,words=len(a),starts=len(a)-w+1,lengths_sha256=ah(a)) for n,a in sorted(C.items()) if w<=len(a)<2928] for w in (400,120)}
    assert [len(selected[str(w)]) for w in (400,120)]==[8,10]
    assert [sum(r['starts'] for r in selected[str(w)]) for w in (400,120)]==[5378,8037]
    pins={p.relative_to(H).as_posix():sha(p.read_bytes()) for p in sorted(H.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    write(H/'protocol-frozen.json',dict(version=1,pins=pins,patterns=pin_patterns(pats),selected=selected,alignment_scores=40245,seed=3301,rng='Consume four full2928 permutations, then two400 and two120 permutations exactly as unchanged run_scan.main.',source='Unmodified scanner.scan_corpus; separate3-pattern calls width400 then120, default block131072/FFT262144, only newly eligible texts; exact original94 inputmanifest/parser.',controls_sha256=sha((H/'controls.json').read_bytes()),selection='Sorted text order; raw float argmax, strict > across blocks/texts as source. Integer tie sets separately reported; no rounding to select.',decision='A complete prefix match requires integer count equal width. Partial interval counts are not plaintext. No significance gate, only two fixed shuffled patterns each. No global probability, full2928 rescan, historical224-text or changed editions.',outputs='All40245 float64 FFT scores and int16 direct counts; per-text/global winners with offsets, integer ties and array hashes; original84 maxima only as separately identified reused evidence if exact pattern hashes verified.'))
    print('Protocol frozen',sha((H/'protocol-frozen.json').read_bytes()),flush=True)
def target(inputs,output):
    protocol=read(H/'protocol-frozen.json')
    for p,h in protocol['pins'].items():assert sha((H/p).read_bytes())==h,p
    sk,sc,C,pats=load(inputs);assert pin_patterns(pats)==protocol['patterns'];output=Path(output)
    if output.exists():raise ValueError('Output directory must be new')
    output.mkdir(parents=True);start=time.perf_counter();rows=[];arrays={};groups=[];total=0
    for w in (400,120):
        selected={r['name']:C[r['name']] for r in protocol['selected'][str(w)]};pp={n:v for n,v in pats.items() if len(v[0])==w};ps=compiled(sk,sc,pp)
        best,per=sc.scan_corpus(selected,ps);groups.append(dict(width=w,best={n:dict(count=b[0],text=b[1],offset=b[2]) for n,b in best.items()},per_text=per))
        for ti,(text,a) in enumerate(sorted(selected.items())):
            raw=sc.scan_block(a,ps)
            for pi,(n,(o,f)) in enumerate(pp.items()):
                ints=direct(a,o,f);v=raw[n];assert np.max(np.abs(v-ints))<.01;j=int(v.argmax());assert v[j]==per[n][text] and ints[j]==ints.max()
                key=f'w{w}_t{ti}_p{pi}';arrays[key+'_fft']=v;arrays[key+'_integer']=ints;total+=len(v)
                rows.append(dict(key=key,pattern=n,text=text,words=len(a),starts=len(v),offset=j,raw_max=float(v[j]),integer_max=int(ints.max()),integer_ties=np.flatnonzero(ints==ints.max()).tolist(),selected_integer=int(ints[j]),max_fft_error=float(np.max(np.abs(v-ints))),complete=int(ints.max())==w))
        print('Completed width',w,'texts',len(selected),'elapsed',time.perf_counter()-start,flush=True)
    assert total==40245
    np.savez_compressed(output/'alignment-scores.npz',**arrays)
    write(output/'results.json',dict(protocol_sha256=sha((H/'protocol-frozen.json').read_bytes()),alignment_scores=total,groups=groups,per_text_winners=rows,complete_real_prefix_matches=sum(r['complete'] for r in rows if r['pattern'].startswith('real')),score_arrays_sha256=sha((output/'alignment-scores.npz').read_bytes()),seconds=time.perf_counter()-start,numpy=np.__version__))
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['controls','freeze','target']);p.add_argument('--inputs',required=True);p.add_argument('--output');a=p.parse_args()
    if a.command=='controls':controls(a.inputs)
    elif a.command=='freeze':freeze(a.inputs)
    else:target(a.inputs,a.output)
if __name__=='__main__':main()
