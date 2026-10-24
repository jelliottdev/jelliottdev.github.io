"""Private faithful held-corpus replay. Corpus bytes are referenced, never copied."""
import sys, json, hashlib, glob, subprocess, time, contextlib, importlib
from pathlib import Path
sys.dont_write_bytecode = True
import numpy as np
H = Path(__file__).resolve().parent
REPO = H.parents[2]
SOURCE = REPO.parent / 'source-cache/dukotah-cicada3301'
BASE = SOURCE / 'liber-primus/analysis/round10/L4-skeleton'
REV = 'f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
sys.path.insert(0, str(BASE))
import skel, scanner
sha = lambda b: hashlib.sha256(b).hexdigest()
def write(name, obj):
    p = H/name
    assert not p.exists(), 'Refusing overwrite: '+str(p)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
def read(name): return json.loads((H/name).read_text(encoding='utf-8'))
def ah(a): return sha(a.astype('<i2').tobytes())
def inputs():
    pins=[]
    for f in ['scanner.py','skel.py','run_scan.py','positive_control.py','PREREG.md','RESULTS.md','../../../src/lp/gematria.py']:
        p=(BASE/f).resolve(); rel=p.relative_to(SOURCE).as_posix(); raw=p.read_bytes()
        assert raw == subprocess.check_output(['git','-C',str(SOURCE),'show',REV+':'+rel])
        pins.append(dict(path=rel,bytes=len(raw),sha256=sha(raw)))
    rows=[]; selected={}; seen=set(); excluded=[]
    for pat,tag in skel.SOURCES:
        for filename in sorted(glob.glob(pat,recursive=True)):
            p=Path(filename)
            if p.name in skel.SKIP: continue
            raw=p.read_bytes(); a=skel.corpus_lengths(skel.clean(raw.decode('utf-8',errors='ignore'),str(p)))
            if len(a)<300:
                excluded.append(dict(path=p.relative_to(SOURCE).as_posix(),words=len(a),sha256=sha(raw))); continue
            key=tag+'/'+p.name; digest=hashlib.sha1(a.tobytes()).hexdigest()
            assert key not in selected and digest not in seen
            selected[key]=a;seen.add(digest)
            rows.append(dict(name=key,path=p.relative_to(SOURCE).as_posix(),bytes=len(raw),sha256=sha(raw),words=len(a),lengths_sha256=ah(a)))
    C,_=skel.load_corpus(verbose=False)
    assert list(C)==list(selected) and all(np.array_equal(C[k],selected[k]) for k in C)
    assert len(C)==94 and sum(map(len,C.values()))==9808699
    lp,fc=skel.lp2_words(); p=Path(skel.ROOT)/'data/krisyotam_runes.txt'
    prior=REPO/'research/source-intake/hint-scope-cohort-2026-10-23'
    return dict(revision=REV,source_files=pins,corpus=rows,excluded_below_300=excluded,corpus_words=sum(map(len,C.values())),manuscript=dict(path=p.relative_to(SOURCE).as_posix(),sha256=sha(p.read_bytes()),segments='first 55 percent-separated source segments',words=len(lp),lengths_sha256=ah(lp),fcounts_sha256=ah(fc)),prior_controls=[dict(path=(prior/f).relative_to(REPO).as_posix(),sha256=sha((prior/f).read_bytes())) for f in ['scanner-plan-frozen.json','scanner-results.json','scanner-control.py','check-scanner.py']]),C
def verify():
    current,C=inputs(); assert current==read('inputs-frozen.json'), 'Pinned inputs changed'; return C
def controls():
    p=read('controls-plan-frozen.json');verify();rng=np.random.default_rng(p['seed']); rows=[];total=0;t=time.perf_counter()
    for W in p['windows']:
        for off in [0,2048,5000-W]:
            a=rng.integers(1,16,5000,dtype=np.int16);fc=rng.integers(0,4,W,dtype=np.int16);obs=a[off:off+W]+fc
            pats=[scanner.Pattern('exact',skel.groups_slack(obs,0),W,8192),scanner.Pattern('slack1',skel.groups_slack(obs,1),W,8192),scanner.Pattern('interval',skel.groups_interval(obs,fc),W,8192)]
            best,_=scanner.scan_corpus({'synthetic':a},pats,block=4096,size=8192);fft=scanner.scan_block(a,pats,size=8192)
            windows=np.lib.stride_tricks.sliding_window_view(a,W)
            direct={'exact':(windows==obs).sum(axis=1),'slack1':(np.abs(windows.astype(np.int32)-obs)<=1).sum(axis=1),'interval':((windows>=obs-fc)&(windows<=obs)).sum(axis=1)}
            matchers={}
            for k,v in direct.items():
                assert np.max(np.abs(fft[k]-v))<.01
                assert abs(best[k][0]-v.max())<.01 and v[best[k][2]]==v.max()
                if k=='interval': assert v[off]==W
                total+=len(v);matchers[k]=dict(maximum=int(v.max()),truth_count=int(v[off]),blocked_offset=best[k][2],offsets=len(v),counts_sha256=sha(v.astype('<i8').tobytes()))
            rows.append(dict(window=W,truth_offset=off,matchers=matchers))
    a=rng.integers(1,16,131072,dtype=np.int16);obs=rng.integers(1,18,2928,dtype=np.int16);fc=rng.integers(0,4,2928,dtype=np.int16)
    pats=[scanner.Pattern('exact',skel.groups_slack(obs,0),2928),scanner.Pattern('slack1',skel.groups_slack(obs,1),2928),scanner.Pattern('interval',skel.groups_interval(obs,fc),2928)]
    b=time.perf_counter();scanner.scan_corpus({'synthetic':a},pats);elapsed=time.perf_counter()-b
    write('independent-controls.json',dict(plan_sha256=sha((H/'controls-plan-frozen.json').read_bytes()),cases=rows,independent_offset_counts=total,elapsed_seconds=time.perf_counter()-t,production_block_benchmark=dict(patterns=3,words=len(a),seconds=elapsed,description='Synthetic arrays only; no manuscript patterns')))
    print('PASS independent controls:',total,'offset counts; production block',round(elapsed,3),'seconds',flush=True)
def source_run(which):
    verify();name='positive_control' if which=='t0' else 'run_scan';out='positive_control_T0.json' if which=='t0' else 'scan_results.json'
    assert not (H/out).exists()
    plan=read('target-plan-frozen.json' if which=='target' else 'controls-plan-frozen.json')
    assert plan['inputs_sha256']==sha((H/'inputs-frozen.json').read_bytes())
    module=importlib.import_module(name);module.HERE=str(H);sys.argv=[name+'.py']+(['T0'] if which=='t0' else [])
    start=time.perf_counter()
    with (H/(which+'-stdout.txt')).open('x',encoding='utf-8',newline='\n') as f:
        class Tee:
            def write(self,s): sys.__stdout__.write(s);f.write(s)
            def flush(self): sys.__stdout__.flush();f.flush()
        with contextlib.redirect_stdout(Tee()): module.main()
    write(which+'-runtime.json',dict(seconds=time.perf_counter()-start,source_module=name,source_main_unchanged=True,adaptation='HERE redirected to this private folder; argv fixed to T0 or no extra corpus globs',output_sha256=sha((H/out).read_bytes())))
    print('Completed',which,flush=True)
def freeze_target():
    verify();read('independent-controls.json');plants=[r for r in read('positive_control_T0.json')['results'] if r['truth']]
    assert len(plants)==6 and all(r['text']==r['truth']['text'] and r['offset']==r['truth']['offset'] for r in plants)
    assert all(abs(r['best']-r['window'])<.01 for r in plants if r['pattern'].endswith(':interval'))
    write('target-plan-frozen.json',dict(inputs_sha256=sha((H/'inputs-frozen.json').read_bytes()),controls_sha256=sha((H/'independent-controls.json').read_bytes()),t0_sha256=sha((H/'positive_control_T0.json').read_bytes()),runner_sha256=sha(Path(__file__).read_bytes()),source='Unchanged run_scan.main; no extra globs; default scanner blocks and FFT size',seed=3301,patterns='3 full real +4 full permutations x3 matchers; first400 and first120 each interval +2 permutations =21',selection='All94 held texts loaded; source skips every text shorter than full2928 even for prefixes. Report eligible texts and unique alignments separately.',analysis='Preserve floating maxima/ties; independently reconstruct21 patterns and recount global winning witnesses; check per-text membership/integer bounds, not independent exhaustive FFT maxima.',limits='Not historical224text replay. Only source first55segments and two fixed prefixes. Four/two shuffled controls are descriptive, no calibrated global p or general language/plaintext rejection. No T0b/c degradation-floor replay.',frozen_at_utc=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()))
    print('Frozen target plan after controls; no target run yet')
def audit():
    C=verify();lp,fc=skel.lp2_words();P=len(lp);rng=np.random.default_rng(3301);patterns={}
    for tag,obs,f in [('real',lp,fc)]+[(f'n{k}',lp[(i:=rng.permutation(P))],fc[i]) for k in range(4)]:
        for mode in ['exact','slack1','interval']: patterns[tag+':'+mode]=(obs,f,mode)
    for W in [400,120]:
        patterns[f'realW{W}:interval']=(lp[:W],fc[:W],'interval')
        for k in range(2):
            i=rng.permutation(W);patterns[f'n{k}W{W}:interval']=(lp[:W][i],fc[:W][i],'interval')
    results=read('scan_results.json');rows=[];eligible={k:a for k,a in C.items() if len(a)>=P}
    for name,(obs,f,mode) in patterns.items():
        r=results['best'][name];a=C[r['text']][r['offset']:r['offset']+len(obs)]
        n=int((a==obs).sum()) if mode=='exact' else int((np.abs(a.astype(np.int32)-obs)<=1).sum()) if mode=='slack1' else int(((a>=obs-f)&(a<=obs)).sum())
        assert abs(n-r['count'])<.01 and r['text'] in eligible
        assert set(results['per_text'][name])==set(eligible)
        assert all(abs(v-round(v))<.01 and 0<=round(v)<=len(obs) for v in results['per_text'][name].values())
        rows.append(dict(pattern=name,window=len(obs),count=n,text=r['text'],offset=r['offset'],unique_eligible_alignments=sum(len(a)-len(obs)+1 for a in eligible.values()),fraction=n/len(obs)))
    write('independent-target-audit.json',dict(target_plan_sha256=sha((H/'target-plan-frozen.json').read_bytes()),output_sha256=sha((H/'scan_results.json').read_bytes()),eligible_texts=len(eligible),eligible_words=sum(map(len,eligible.values())),omitted_short_texts=[dict(text=k,words=len(a)) for k,a in C.items() if len(a)<P],global_witnesses=rows,checks='Independent direct comparisons recount all21 global witnesses; per-text membership/bounds/integer checks only, not independent full FFT maxima. Source floating ties retained. No corpus snippets included.'))
    print('PASS21 global witness recounts; eligible texts',len(eligible),flush=True)
if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='freeze-controls':
        manifest,C=inputs();write('inputs-frozen.json',manifest)
        write('controls-plan-frozen.json',dict(seed=330120261024,windows=[120,400,2928],corpus_length=5000,offsets=[0,2048,'5000-W'],block=4096,size=8192,matchers=['exact','slack1','interval'],checks='Independent direct per-offset counts against unchanged source FFT and blocked maxima. Interval planted truth equals W. Then source T0 over same held corpus. No manuscript target scores.',inputs_sha256=sha((H/'inputs-frozen.json').read_bytes()),runner_sha256=sha(Path(__file__).read_bytes())))
        print('Pinned94 texts; controls frozen')
    elif cmd=='controls': controls()
    elif cmd in ['t0','target']: source_run(cmd)
    elif cmd=='freeze-target': freeze_target()
    elif cmd=='audit': audit()
