"""Replay the keyword-plus-position-ramp branch of the pinned Wulfic source."""
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
def read_source(src,rev,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',rev+':'+path])
    assert sha(b)==want,(path,sha(b),want)
    return b
def source_module(src,plan):
    b=read_source(src,plan['source_revision'],plan['source_script'],plan['source_script_sha256'])
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'source.py';p.write_bytes(b)
        spec=importlib.util.spec_from_file_location('source',p)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def arrays(src,plan):
    ans={}
    for q in plan['pages']:
        raw=read_source(src,plan['source_revision'],q['source_path'],q['source_sha256']).decode('utf8')
        site=(ROOT/q['site_path']).read_bytes();assert sha(site)==q['site_sha256']
        s=json.loads(site);a=[R[c] for c in s['raw'] if c in R]
        b=[R[c] for c in raw if c in R]
        assert a==b,(q['source_page'],len(a),len(b))
        ans[q['source_page']]=a
    return ans
def compute(src):
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    m=source_module(src,plan)
    assert set(plan['steps'])=={1,2,3,5,7,11,13,-1,-2}
    for q in plan['pages']:
        assert list(m.PAGE_KEYWORDS[q['source_page']][1])==q['seed']
    a=arrays(src,plan)
    known_bytes=(ROOT/plan['known_readings_path']).read_bytes()
    assert sha(known_bytes)==plan['known_readings_sha256']
    known=json.loads(known_bytes)
    p=next(x for x in known['controls'] if x['id']==plan['control']['reading'])['decoded_pages'][0]['rune_indices']
    seed=plan['pages'][0]['seed'];step=plan['control']['planted_step']
    c=[(v+seed[i%len(seed)]+i*step)%29 for i,v in enumerate(p)]
    planted=[]
    for s in plan['steps']:
        dec=m.progressive_key(c,seed,s)
        planted.append({'step':s,'exact':dec==p,'score':m.score_text(m.to_runeglish(dec)),
                        'ioc':m.compute_ioc(dec),'decoded_sha256':sha(bytes(dec))})
    best_control=max(row['score'] for row in planted)
    assert sum(row['exact'] for row in planted)==1
    assert next(row['score'] for row in planted if row['exact'])==best_control
    observed=[]
    for q in plan['pages']:
        page=q['source_page'];seed=q['seed']
        for s in plan['steps']:
            dec=m.progressive_key(a[page],seed,s)
            observed.append({'page':q['site_page'],'source_page':page,'step':s,
                             'score':m.score_text(m.to_runeglish(dec)),
                             'ioc':m.compute_ioc(dec),'decoded_sha256':sha(bytes(dec))})
    rng=random.Random(plan['null']['seed']);null=[]
    for t in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=list(a[q['source_page']]);rng.shuffle(x);shuffled[q['source_page']]=x
        maxi=max(m.score_text(m.to_runeglish(m.progressive_key(shuffled[q['source_page']],q['seed'],s)))
                 for q in plan['pages'] for s in plan['steps'])
        null.append(maxi)
    top=max(observed,key=lambda row:row['score'])
    return {'schema':'wulfic-keyword-ramp-results-v1','plan_sha256':sha((HERE/'plan.json').read_bytes()),
            'observed':observed,'control':{'reading':'first-koan','length':len(p),'cases':planted},
            'null_maxima':null,'summary':{'top':top,'observed_max':top['score'],
                 'null_at_least_observed':sum(v>=top['score'] for v in null),
                 'null_trials':len(null),'cases':len(observed)}}
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=pathlib.Path,default=DEFAULT_SOURCE);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=compute(args.source_root)
    path=HERE/'results.json';encoded=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.check:
        assert path.read_text(encoding='utf8')==encoded
        print('PASS source replay, controls, 199 complete shuffles')
    else:
        path.write_text(encoded,encoding='utf8',newline='\n')
        print(json.dumps(result['summary']))
