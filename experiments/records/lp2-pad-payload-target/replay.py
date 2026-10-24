"""Private F-01 skipped-T5 amendment; fixed source decoder and old-row scope."""
import sys,json,hashlib,shutil,subprocess,importlib.util,ast,time,contextlib,copy,random
from pathlib import Path
sys.dont_write_bytecode=True
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
OLD=ROOT/'experiments/records/public-lp2-as-pad'
SOURCE=H/'source';LP=SOURCE/'liber-primus'
REV='f08b20b632d91209ddbaa747e8e2f23df0c78ba1'
PAYLOAD=ROOT/'experiments/records/public-rsa-payload-e01/source/liber-primus/analysis/pp49_51/canon_256.bin'
TARGET='T5_pp4951'
KEYS=['lp2_fwd','lp2_rev','lp2_atbash','lp2_neg'];SIGNS=[-1,1]
OLDTARGETS=['T1_cicada_2012_2013','T2_lp1_solved','T3_pgp_messages','T4_anend_hash','T6_lp2_head_200']
sha=lambda b:hashlib.sha256(b).hexdigest()
ih=lambda a:sha(','.join(map(str,a)).encode())
def read(name):return json.loads((H/name).read_text(encoding='utf-8'))
def write(name,obj):
    p=H/name;assert not p.exists(),'Refusing overwrite '+str(p)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def verify():
    for item in read('inputs-frozen.json')['files']:
        p=ROOT/item['path'];assert sha(p.read_bytes())==item['sha256'],item['path']
    for item in read('inputs-frozen.json')['staged_source']:
        assert sha((H/item['path']).read_bytes())==item['sha256'],item['path']
def instrument():
    verify();m=load('f01_source',LP/'analysis/round16/F-01/sweep.py');K=m.load_lp2()
    assert len(K)==12956 and ih(K)=='023312066df471005264b9cbe7997cb77d2a9a6a2dc9b3316d22674023af1585'
    variants=dict(lp2_fwd=K,lp2_rev=list(reversed(K)),lp2_atbash=m.atbash(K),lp2_neg=m.neg_mod(K))
    oldtargets=dict(T1_cicada_2012_2013=m.load_cicada_2012_2013(),T2_lp1_solved=m.load_lp1_runes(),T3_pgp_messages=m.load_pgp_messages(),T4_anend_hash=m.load_anend_hash(),T6_lp2_head_200=K[:200])
    assert len(oldtargets['T4_anend_hash'])==63
    payload=m.load_pp4951_payload();assert payload==[b%29 for b in PAYLOAD.read_bytes()] and len(payload)==256
    return m,variants,oldtargets,payload
def source_plain():
    tree=ast.parse((LP/'analysis/round16/F-01/sweep.py').read_text(encoding='utf-8'))
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='positive_control')
    assignment=next(n for n in fn.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PLAIN_TEXT' for t in n.targets))
    return ast.literal_eval(assignment.value)
def freeze():
    assert not SOURCE.exists()
    oldrecord=json.loads((OLD/'record.json').read_text(encoding='utf-8'));pins=[]
    for item in oldrecord['reproduction']['inputs']:
        p=ROOT/item['path'];assert sha(p.read_bytes())==item['sha256'];pins.append(copy.deepcopy(item))
    output=OLD/'source/liber-primus/analysis/round16/F-01/results.json'
    pins.extend([dict(path=output.relative_to(ROOT).as_posix(),sha256=sha(output.read_bytes())),dict(path=(OLD/'record.json').relative_to(ROOT).as_posix(),sha256=sha((OLD/'record.json').read_bytes())),dict(path=PAYLOAD.relative_to(ROOT).as_posix(),sha256=sha(PAYLOAD.read_bytes()))])
    assert len(PAYLOAD.read_bytes())==256 and sha(PAYLOAD.read_bytes())=='4c8dc85531d256793a6d0d318b8845869b4983e672077b094ed955bde92226d5'
    gitroot=ROOT.parent/'source-cache/dukotah-cicada3301'
    assert PAYLOAD.read_bytes()==subprocess.check_output(['git','-C',str(gitroot),'show',REV+':liber-primus/analysis/pp49_51/canon_256.bin'])
    shutil.copytree(OLD/'source',SOURCE,ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo'))
    amended=LP/'analysis/pp49_51/payload.bin';amended.parent.mkdir(parents=True,exist_ok=True);amended.write_bytes(PAYLOAD.read_bytes())
    staged=[dict(path=p.relative_to(H).as_posix(),sha256=sha(p.read_bytes()),bytes=p.stat().st_size) for p in sorted(SOURCE.rglob('*')) if p.is_file()]
    write('inputs-frozen.json',dict(source_id='F-01',source_revision=REV,files=pins,staged_source=staged,payload_amendment='Supply the committed canon_256 bytes at the first source loader candidate payload.bin; historical payload.bin bytes/provenance were unavailable. No other input/source change.',payload_raw_sha256=sha(PAYLOAD.read_bytes()),old_an_end_bytes_preserved=63))
    m,V,T,C=instrument();plain=source_plain();P=m.sk.eng_to_idx(plain);P256=(P*((256+len(P)-1)//len(P)))[:256]
    labels=[dict(key_variant=k,sign=s,signed_key_sha256=ih([(s*x)%29 for x in V[k]])) for k in KEYS for s in SIGNS]
    write('preflight-plan-frozen.json',dict(inputs_sha256=sha((H/'inputs-frozen.json').read_bytes()),runner_sha256=sha(Path(__file__).read_bytes()),labelled_cases=labels,effective_signed_keys=len({x['signed_key_sha256'] for x in labels}),source_rule=dict(beam_w=400,max_skip=3,offset=0,score_bar=-5.5,null_margin=.5,full_selection_top=5,null_draws=200,null_seed=3301),controls=dict(original_source='Call unchanged positive_control with100 source shuffles; retain actual80% character gate separately from exact rune recovery.',full256_plain='Repeat source positive_control eng_to_idx sequence cyclically, truncate exactly256runes; no new spelling or corpus.',base_plain_text=plain,full256_indices_sha256=ih(P256),seed=3301,suppression=.83,full_cases=8,power_gate='All8full256 plants must decode completely with exact rune recovery, source score>=-5.5 and no true skip>3; report rigid/source-score criteria separately. Fwd/sign-1 also gets100 source null shuffles and source score/null/rigid margins.',baseline_identity='Recompute all40 source primary rows and compare score/head/length/above_bar exactly; check saved original/replay substantive equality. Do not rerun old null panels.',benchmark='Time synthetic256rune decoding; conservatively report max measured per-cell time times possible1000 new source null decodes before targets.'),target_rule='Only supplied canon_256 bytes mod29 as ciphertext; unchanged LP2 variants/signs;8labelledsource calls,6effective signed keys; no offsets or AN END repair.',selection='After new8rows: reconstruct original target/key/sign insertion order including T5 before T6; stable descending score over48. Reuse saved nulls only for selected old rows; compute source200-shuffle panels for newly selected T5 rows, reuse exact signed-key alias panels with explicit labelled/effective work counts.',limits='Source ranks by cumulative quadgram score then reports normalized score. Score gate is not plaintext. Only selected5null panels, not a whole-search calibrated probability. No historical missing-payload bytes recovered.'))
    print('Frozen payload/source/control plan;8labels,6effective signed keys; no target decoding.')
def controls():
    m,V,T,C=instrument();plan=read('preflight-plan-frozen.json');assert plan['runner_sha256']==sha(Path(__file__).read_bytes())
    old=json.loads((LP/'analysis/round16/F-01/results.json').read_text());original=json.loads((LP/'analysis/round16/F-01/original_results.json').read_text())
    assert {k:v for k,v in old.items() if k!='elapsed_s'}=={k:v for k,v in original.items() if k!='elapsed_s'}
    out={};start=time.perf_counter()
    with (H/'controls-stdout.txt').open('x',encoding='utf-8',newline='\n') as f,contextlib.redirect_stdout(f):
        passed,pc=m.positive_control(V['lp2_fwd'],beam_w=400,max_skip=3)
    assert passed and pc==old['positive_control']
    plain=source_plain();base=m.sk.eng_to_idx(plain);P=(base*((256+len(base)-1)//len(base)))[:256];assert ih(P)==plan['controls']['full256_indices_sha256']
    rows=[];times=[]
    for key in KEYS:
        for sign in SIGNS:
            ct,skips,used=m.sk.encipher_keyskip(P,V[key],sign=sign,supp=.83,seed=3301)
            t=time.perf_counter();bd=m.sk.beam_decode(ct,V[key],sign=sign,o=0,beam_w=400,max_skip=3);times.append(time.perf_counter()-t)
            rigid=m.sk.rigid_decode(ct,V[key],sign=sign,o=0)
            row=dict(key_variant=key,sign=sign,length=len(bd['plain_idx']),exact_rune_recovery=bd['plain_idx']==P,rune_recovery=sum(a==b for a,b in zip(P,bd['plain_idx']))/256,score=bd['score'],source_score_bar_pass=bd['score']>=-5.5,rigid_score=rigid['score'],source_rigid_margin_pass=bd['score']>rigid['score']+.5,total_true_skips=sum(skips),max_true_skip=max(skips),true_used_last=used[-1],decoded_ptr_end=bd['ptr_end'],ciphertext_sha256=ih(ct),plain_sha256=ih(bd['plain_idx']),decode_seconds=times[-1])
            if key=='lp2_fwd' and sign==-1:
                mean,maximum,_=m.null_band_beam(ct,V[key],sign=sign,n=100,seed0=3301,beam_w=400,max_skip=3)
                row.update(null_draws=100,null_mean=mean,null_max=maximum,source_null_margin_pass=bd['score']>=maximum+.5)
            rows.append(row)
    baseline=[]
    indexed={(r['target'],r['key_variant'],r['sign']):r for r in old['results']}
    for target in OLDTARGETS:
        ct=T[target][:500]
        for key in KEYS:
            for sign in SIGNS:
                bd=m.sk.beam_decode(ct,V[key],sign=sign,o=0,beam_w=400,max_skip=3)
                got=dict(target=target,target_len=len(ct),key_variant=key,sign=sign,score=bd['score'],head=bd['translit'][:60],above_bar=bd['score']>=-5.5)
                assert all(indexed[(target,key,sign)][k]==v for k,v in got.items()),(target,key,sign)
                baseline.append(got)
    support=passed and all(r['length']==256 and r['exact_rune_recovery'] and r['source_score_bar_pass'] and r['max_true_skip']<=3 for r in rows)
    fwd=next(r for r in rows if r['key_variant']=='lp2_fwd' and r['sign']==-1)
    support=support and fwd['source_null_margin_pass'] and fwd['source_rigid_margin_pass']
    write('control-results.json',dict(preflight_plan_sha256=sha((H/'preflight-plan-frozen.json').read_bytes()),source_original_control=pc,source_original_gate_pass=passed,full256_controls=rows,old40_primary_rows_equal=True,old40_rows=baseline,target_power_gate_pass=support,elapsed_seconds=time.perf_counter()-start,synthetic_max_decode_seconds=max(times),conservative_1000null_seconds=max(times)*1000,scope='Original gate preserved; exact256rune recovery is a separately frozen extra control. No T5targetdecoded.'))
    print('Controls complete; original source gate',passed,'full256power gate',support,'max synthetic decode',round(max(times),4),'seconds; old40rows exactly equal',flush=True)
def freeze_target():
    verify();control=read('control-results.json');assert control['target_power_gate_pass'],'Control failed: stop for review'
    write('target-plan-frozen.json',dict(preflight_plan_sha256=sha((H/'preflight-plan-frozen.json').read_bytes()),control_results_sha256=sha((H/'control-results.json').read_bytes()),inputs_sha256=sha((H/'inputs-frozen.json').read_bytes()),runner_sha256=sha(Path(__file__).read_bytes()),target='Only supplied canon_256 ->byte%29,256runes;8source labels,6effective keys; exactsource beam400/max_skip3,offset0.',selection='Unchanged stable source ranking over merged48 labels; T5 inserted before T6. Reuse old selected nulls; source200shuffles seed3301 for newly selected T5labels, exact signed-key aliases share one actual panel but retain source labelled counts.',witness='Save full plaintextindices/transliteration,ptr_end,cumulative+normalizedscores for8newlabels. Independent raw-quadgram rescore and admissible key-index trace for selected best T5; no general English/plaintext assertion.',time_budget_note='Synthetic benchmark and old40identity passed before targets; no threshold tuning or other payload variants.'))
    print('Target plan frozen; no T5targetdecode yet.')
def target():
    m,V,T,C=instrument();plan=read('target-plan-frozen.json');assert plan['runner_sha256']==sha(Path(__file__).read_bytes())
    assert plan['control_results_sha256']==sha((H/'control-results.json').read_bytes());start=time.perf_counter();new=[];witness=[]
    for key in KEYS:
        for sign in SIGNS:
            bd=m.sk.beam_decode(C,V[key],sign=sign,o=0,beam_w=400,max_skip=3)
            new.append(dict(target=TARGET,target_len=len(C),key_variant=key,sign=sign,score=bd['score'],head=bd['translit'][:60],above_bar=bd['score']>=-5.5))
            witness.append(dict(key_variant=key,sign=sign,**bd))
            print(key,sign,round(bd['score'],6),'length',len(bd['plain_idx']),flush=True)
    old=json.loads((LP/'analysis/round16/F-01/results.json').read_text());index={(r['target'],r['key_variant'],r['sign']):r for r in old['results']};newindex={(r['key_variant'],r['sign']):r for r in new}
    rows=[]
    for target_name in OLDTARGETS[:-1]+[TARGET,OLDTARGETS[-1]]:
        for key in KEYS:
            for sign in SIGNS:
                source=newindex[(key,sign)] if target_name==TARGET else index[(target_name,key,sign)]
                rows.append({k:source[k] for k in ['target','target_len','key_variant','sign','score','head','above_bar']})
    rows.sort(key=lambda r:-r['score']);panels=[];cache={};actual_null_decodes=0
    for row in rows[:5]:
        if row['target']!=TARGET:
            oldrow=index[(row['target'],row['key_variant'],row['sign'])];assert 'null_max' in oldrow
            row.update({k:oldrow[k] for k in ['null_mean','null_max','beats_null_by','hit']});panels.append(dict(target=row['target'],key_variant=row['key_variant'],sign=row['sign'],reused_old=True,actual_new_decodes=0));continue
        alias=ih([(row['sign']*x)%29 for x in V[row['key_variant']]])
        if alias not in cache:
            mean,maximum,values=m.null_band_beam(C,V[row['key_variant']],row['sign'],200,3301,400,3);cache[alias]=(mean,maximum,values);actual_null_decodes+=200;reused=False
        else:mean,maximum,values=cache[alias];reused=True
        row.update(null_mean=mean,null_max=maximum,beats_null_by=row['score']-maximum,hit=row['score']>=-5.5 and row['score']>=maximum+.5)
        panels.append(dict(target=TARGET,key_variant=row['key_variant'],sign=row['sign'],reused_alias=reused,actual_new_decodes=0 if reused else 200,null_scores=values))
    write('target-results.json',dict(target_plan_sha256=sha((H/'target-plan-frozen.json').read_bytes()),new_labelled_rows=new,new_effective_keys=6,combined_labelled_rows=rows,new_witnesses=witness,selected_null_panels=panels,actual_new_null_decodes=actual_null_decodes,any_source_hit=any(r.get('hit',False) for r in rows),elapsed_seconds=time.perf_counter()-start,amendment='Committed canon_256 supplied at source payload.bin path; not historical unknown payload bytes.'))
    print('Target complete; new8labels, combined48labels; newly executed null decodes',actual_null_decodes,'source hit',any(r.get('hit',False) for r in rows),flush=True)
if __name__=='__main__':
    command=sys.argv[1]
    if command=='freeze':freeze()
    elif command=='controls':controls()
    elif command=='freeze-target':freeze_target()
    elif command=='target':target()
