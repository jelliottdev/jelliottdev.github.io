"""Freeze numeric source grids, then benchmark source-only synthetic controls.

No function in this module loads or decodes manuscript target pages.
"""
import argparse,csv,hashlib,importlib.util,json,sys,time
from pathlib import Path
import numpy as np
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SRC=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
def load():
    sys.path[:0]=[str(SRC/'analysis/campaign18_skip/armada'),str(SRC/'analysis/campaign18_skip/armada2'),str(SRC/'analysis/campaign18_skip'),str(SRC/'analysis'),str(SRC/'src')]
    import numeric_skip as a,numeric2_skip as b,skipdecode as enc,sweep
    streams=[('numeric',n,list(map(int,k))) for n,k in a.build_catalog(1176,include_fib=False)]
    streams += [('numeric2A',n,list(map(int,k))) for n,k in b.build_fixed_catalog(1172)]
    assert len(streams)==54
    return a,b,enc,sweep,streams
def freeze():
    assert not (HERE/'plan-frozen.json').exists()
    a,b,e,s,streams=load()
    warning=json.loads((ROOT/'experiments/records/d04-remaining-page-feedback/warning.json').read_text(encoding='utf-8'))
    known=[int(row['output_index']) for row in csv.DictReader((ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8-sig',newline=''))]
    write(HERE/'known-readings.json',{'warning':warning,'lp2-56':known})
    write(HERE/'streams.json',[{'branch':br,'name':n,'key':k} for br,n,k in streams])
    files=['analysis/campaign18_skip/armada/numeric_skip.py','analysis/campaign18_skip/armada2/numeric2_skip.py','analysis/campaign18_skip/sweep.py','analysis/campaign18_skip/skipdecode.py','analysis/run_stats.py','src/lp/gematria.py','src/lp/score.py','data/english_quadgrams.txt','data/krisyotam_runes.txt','data/keys/solved_plaintext.txt','data/keys/self_reliance.txt','analysis/pp49_51/canon_256.hex']
    plan={'revision':'f08b20b632d91209ddbaa747e8e2f23df0c78ba1','frozen_before':'synthetic controls and any local target run','license':'source repository MIT; preserve attribution','source_root_relative_to_repo':'../source-cache/dukotah-cicada3301/liber-primus','source_hashes':{p:sha(SRC/p) for p in files},'local_hashes':{p:sha(HERE/p) for p in ['known-readings.json','streams.json']},'stream_labels':[br+':'+n for br,n,k in streams],'target_grid':{'numeric':{'streams':33,'key_length':1176,'full_beam':200,'screens':36300},'numeric2A':{'streams':21,'key_length':1172,'full_beam':300,'screens':23100},'shared':{'pages':'55 nonempty source segments mapping LP2-00..49,51..55','signs':[-1,1],'atbash':[0,1],'offsets':[0,1,2,3,4],'screen_length':50,'screen_beam':60,'screen_strict_threshold':-6.5,'full_strict_threshold':-5.5,'max_skip':3,'confirmation_only_after_screen':True}},'overlap':{'dukotah-fixed-numeric-keys':'Some identical numeric artifacts; different rigid/F clocks, starts zero, score bar -5.2. New skip search explicitly overlaps values, not established decoding coverage.','typed-seed-random-opening-cribs':'Some seed/PRNG overlap; fixed opening crib criterion, not these skip beam English gates.','d04-remaining-page-feedback':'numeric_skip imported as dependency, catalog never executed.','r18-drift-ladder-skip-channel-replay':'Previously selected 230 text keys and offset-band prefix search, not either numeric catalog.','newest_pair_and_turtle':'Page-as-pad and turtle geometry are different rules; no numeric-catalog target replay found.'},'controls':{'grid':'all 54 labels x signs [-1,+1] x Atbash [0,1] x offsets [0..4] =1080 cells','reading':'warning (184 runes) when (stream_index+offset)%2==0, otherwise LP2-56 (85 runes)','encoder':'unchanged skipdecode.encipher_keyskip; K[offset:], supp=.83; seed candidates 3301..3332; use first with max(skip_counts)<=3, report attempts and original max. No target-based selection.','full_decode':'unchanged sweep.beam at branch full width even if source screen fails; diagnostic only, source selected-full separately counted','wrong_key':'next labelled stream whose complete key differs; same sign, Atbash,offset, widths; no target search','report':'exact whole reading recovery; exact first50 recovery; screen score and passage; full score and passage; actual skip counts/max; wrong-key scores; timings. Report no-eligible plant and zero-skip plants explicitly.'},'benchmark':'source-only synthetic control timings; no acceleration proposed; project total screens by mean/max per-branch timing, confirmations separately; no manuscript target run authorized'}
    write(HERE/'plan-frozen.json',plan)
    print('FROZEN 54 labelled streams; 1080 synthetic control cells; no target decoded',flush=True)
def probe():
    plan=json.loads((HERE/'plan-frozen.json').read_text(encoding='utf-8'))
    for p,h in plan['source_hashes'].items():assert sha(SRC/p)==h,p
    for p,h in plan['local_hashes'].items():assert sha(HERE/p)==h,p
    a,b,enc,s,streams=load();known=json.loads((HERE/'known-readings.json').read_text(encoding='utf-8'));rows=[];started=time.perf_counter()
    for ix,(branch,name,K) in enumerate(streams):
        width=200 if branch=='numeric' else 300
        wrong=next(kk for _,_,kk in streams[ix+1:]+streams[:ix+1] if kk!=K)
        for sign in [-1,1]:
            for atb in [0,1]:
                for off in range(5):
                    reading='warning' if (ix+off)%2==0 else 'lp2-56';P=known[reading];C=None;initial=None
                    for seed in range(3301,3333):
                        cc,sk,used=enc.encipher_keyskip(P,K[off:],sign=sign,supp=.83,seed=seed)
                        if initial is None:initial=max(sk)
                        if max(sk)<=3:C=cc;break
                    row={'branch':branch,'name':name,'sign':sign,'atbash':atb,'offset':off,'reading':reading,'initial_max_skip':initial,'eligible':C is not None,'attempts':seed-3300}
                    if C is not None:
                        raw=np.array(C,np.int64);raw=28-raw if atb else raw;ct=28-raw if atb else raw;assert ct.tolist()==C
                        t=time.perf_counter();short=s.beam(ct,np.array(K),sign,off,50,60);st=time.perf_counter()-t
                        t=time.perf_counter();full=s.beam(ct,np.array(K),sign,off,len(P),width);ft=time.perf_counter()-t
                        ws=s.beam(ct,np.array(wrong),sign,off,50,60);wf=s.beam(ct,np.array(wrong),sign,off,len(P),width)
                        score=lambda p:s.Q.score_norm(enc.idx_to_trans(p))
                        ss,fs=score(short),score(full)
                        row.update(seed=seed,skip_total=sum(sk),skip_max=max(sk),skip_positions=[j for j,v in enumerate(sk) if v],skips=sk,screen_exact=short==P[:50],full_exact=full==P,screen_score=ss,screen_pass=ss> -6.5,full_score=fs,full_pass=fs> -5.5,source_selected_full=ss> -6.5,source_success=ss> -6.5 and fs> -5.5,wrong_screen_score=score(ws),wrong_full_score=score(wf),screen_seconds=st,full_seconds=ft,cipher_sha256=hashlib.sha256(bytes(raw)).hexdigest(),decoded_sha256=hashlib.sha256(bytes(full)).hexdigest())
                    rows.append(row)
        print(branch,name,'done',round(time.perf_counter()-started,1),'seconds',flush=True)
    write(HERE/'control-results.json',{'plan_sha256':sha(HERE/'plan-frozen.json'),'probe_sha256':sha(HERE/'probe.py'),'elapsed_seconds':time.perf_counter()-started,'rows':rows})
    print('DONE',len(rows),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','probe']);args=ap.parse_args();freeze() if args.mode=='freeze' else probe()
