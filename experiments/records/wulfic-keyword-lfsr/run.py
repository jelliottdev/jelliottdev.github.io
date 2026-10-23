"""Replay the pinned Wulfic keyword-seeded LFSR branch, with a prior power gate."""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import random
import subprocess
import tempfile

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEFAULT_SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
R={c:i for i,c in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path])
    assert sha(b)==want,(path,sha(b),want)
    return b
def source_module(src,plan):
    b=blob(src,plan,plan['source_script'],plan['source_script_sha256'])
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'source.py';p.write_bytes(b)
        spec=importlib.util.spec_from_file_location('source',p)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def load(src,plan):
    m=source_module(src,plan);a={}
    for q in plan['pages']:
        assert list(m.PAGE_KEYWORDS[q['source_page']][1])==q['keyword_indices']
        raw=blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8')
        site=(ROOT/q['site_path']).read_bytes();assert sha(site)==q['site_sha256']
        x=[R[c] for c in json.loads(site)['raw'] if c in R]
        assert x==[R[c] for c in raw if c in R] and len(x)==q['runes']
        a[q['source_page']]=x
    kb=(ROOT/plan['known_readings_path']).read_bytes()
    assert sha(kb)==plan['known_readings_sha256']
    p=next(z for z in json.loads(kb)['controls'] if z['id']==plan['control']['reading'])['decoded_pages'][0]['rune_indices']
    return m,a,p
def cases(plan,m,corpus,keep=True):
    out=[];top=None
    for q in plan['pages']:
        x=corpus[q['source_page']];kw=q['keyword_indices']
        for d in plan['degrees']:
            state=(kw*((d//len(kw))+1))[:d]
            taps_list=[[1,d-1],[1,2],[2,d-1],list(range(1,d))]
            for j,taps in enumerate(taps_list):
                taps=[t for t in taps if t<d]
                k=m.lfsr_key_stream(state,taps,len(x))
                for mode in plan['modes']:
                    y=m.running_key_decrypt(x,k,mode)
                    ioc=m.compute_ioc(y);gated=ioc>1.2
                    score=m.score_text(m.to_runeglish(y)) if gated else None
                    row={'page':q['site_page'],'source_page':q['source_page'],'degree':d,'tap_index':j,'taps':taps,
                         'mode':mode,'ioc':ioc,'reported':gated,'source_score':score,
                         'key_sha256':sha(bytes(k)),'decoded_sha256':sha(bytes(y))}
                    if keep:out.append(row)
                    if gated and (top is None or score+50*ioc>top['source_score']+50*top['ioc']):top=row
    return out,top
def control(plan,m,a,p):
    q=plan['pages'][0];d=plan['control']['degree'];kw=q['keyword_indices']
    state=(kw*((d//len(kw))+1))[:d];taps=[1,d-1]
    k=m.lfsr_key_stream(state,taps,len(p));c=[(v+z)%29 for v,z in zip(p,k)]
    synthetic={q['source_page']:c};rng=random.Random(plan['control']['seed'])
    for other in plan['pages'][1:]:synthetic[other['source_page']]=[rng.randrange(29) for _ in range(other['runes'])]
    rows,top=cases(plan,m,synthetic)
    target=next(z for z in rows if z['source_page']==q['source_page'] and z['degree']==d and z['tap_index']==0 and z['mode']=='sub')
    exact=m.running_key_decrypt(c,k,'sub')==p
    assert exact and target['reported'] and target==top,(exact,target,top)
    return {'reading':plan['control']['reading'],'length':len(p),'cipher_sha256':sha(bytes(c)),
            'plain_sha256':sha(bytes(p)),'true_case':target,'top':top,'reported_cases':sum(z['reported'] for z in rows),
            'whole_grid_cases':len(rows),'exact_recovery':exact}
def compute(src,control_only=False):
    pb=(HERE/'plan.json').read_bytes();plan=json.loads(pb)
    m,a,p=load(src,plan)
    power=control(plan,m,a,p)
    if control_only:return {'schema':'wulfic-keyword-lfsr-control-v1','plan_sha256':sha(pb),'control':power}
    observed,top=cases(plan,m,a)
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=a[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        rows,winner=cases(plan,m,shuffled,keep=False)
        # The source gate may leave the entire 400-case trial unreported.
        null.append(None if winner is None else {'score':winner['source_score']+50*winner['ioc'],
                                                   'reported':True})
    observed_best=None if top is None else top['source_score']+50*top['ioc']
    return {'schema':'wulfic-keyword-lfsr-results-v1','plan_sha256':sha(pb),'control_sha256':sha((HERE/'control-results.json').read_bytes()),
            'control':power,'observed':observed,'null_maxima':null,
            'summary':{'cases':len(observed),'reported':sum(z['reported'] for z in observed),'top':top,
                       'observed_best':observed_best,'null_trials':len(null),
                       'null_reported_trials':sum(z is not None for z in null),
                       'null_at_least_observed':None if top is None else sum(z is not None and z['score']>=observed_best for z in null)}}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT_SOURCE)
    ap.add_argument('--control-only',action='store_true');ap.add_argument('--check',action='store_true');args=ap.parse_args()
    path=HERE/('control-results.json' if args.control_only else 'results.json')
    result=compute(args.source_root,args.control_only);encoded=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.check:assert path.read_text(encoding='utf8')==encoded;print('PASS',path.name)
    else:path.write_text(encoded,encoding='utf8',newline='\n');print(json.dumps(result.get('summary',result['control'])))
