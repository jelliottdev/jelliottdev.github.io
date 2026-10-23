"""Independent arithmetic and source-score check of the complete saved search."""
import argparse
import ast
import collections
import hashlib
import json
import pathlib
import random
import subprocess

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
NAMES=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']
R={c:i for i,c in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,rev,path,want):
    out=subprocess.check_output(['git','-C',str(src),'show',rev+':'+path]);assert sha(out)==want,path;return out
def score(x,words):
    t=''.join(NAMES[v] for v in x)
    return sum(t.count(w)*len(w)**2 for w in words)
def ioc(x):
    n=len(x);f=collections.Counter(x)
    return 29*sum(v*(v-1) for v in f.values())/(n*(n-1)) if n>1 else 0
def decode(x,seed,step):return [(v-seed[i%len(seed)]-i*step)%29 for i,v in enumerate(x)]
def check(src):
    pb=(HERE/'plan.json').read_bytes();plan=json.loads(pb)
    res=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    assert res['plan_sha256']==sha(pb)
    program=blob(src,plan['source_revision'],plan['source_script'],plan['source_script_sha256']).decode('utf8')
    tree=ast.parse(program)
    words=None;source_keys=None
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for target in node.targets:
                if isinstance(target,ast.Name) and target.id=='COMMON_3PLUS':words=ast.literal_eval(node.value)
                if isinstance(target,ast.Name) and target.id=='PAGE_KEYWORDS':source_keys=ast.literal_eval(node.value)
    assert words is not None and source_keys is not None
    corpus={}
    for q in plan['pages']:
        assert source_keys[q['source_page']]==tuple([q['keyword'],q['seed']]) or source_keys[q['source_page']][1]==q['seed']
        sr=blob(src,plan['source_revision'],q['source_path'],q['source_sha256']).decode('utf8')
        site=(ROOT/q['site_path']).read_bytes();assert sha(site)==q['site_sha256']
        sx=[R[c] for c in json.loads(site)['raw'] if c in R]
        assert sx==[R[c] for c in sr if c in R]
        corpus[q['source_page']]=sx
    observed=[]
    for q in plan['pages']:
        for step in plan['steps']:
            x=decode(corpus[q['source_page']],q['seed'],step)
            observed.append({'page':q['site_page'],'source_page':q['source_page'],'step':step,
                             'score':score(x,words),'ioc':ioc(x),'decoded_sha256':sha(bytes(x))})
    assert len(observed)==90
    for a,b in zip(observed,res['observed']):
        assert a.keys()==b.keys()
        for k in a:
            assert abs(a[k]-b[k])<1e-14 if k=='ioc' else a[k]==b[k],(k,a,b)
    kb=(ROOT/plan['known_readings_path']).read_bytes();assert sha(kb)==plan['known_readings_sha256']
    known=json.loads(kb)
    p=next(x for x in known['controls'] if x['id']=='first-koan')['decoded_pages'][0]['rune_indices']
    seed=plan['pages'][0]['seed'];step=plan['control']['planted_step']
    cipher=[(v+seed[i%len(seed)]+i*step)%29 for i,v in enumerate(p)]
    expected=[]
    for s in plan['steps']:
        x=decode(cipher,seed,s)
        expected.append({'step':s,'exact':x==p,'score':score(x,words),'ioc':ioc(x),'decoded_sha256':sha(bytes(x))})
    assert len(p)==res['control']['length'] and expected==res['control']['cases']
    assert sum(v['exact'] for v in expected)==1
    assert next(v['score'] for v in expected if v['exact'])==max(v['score'] for v in expected)
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=corpus[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        null.append(max(score(decode(shuffled[q['source_page']],q['seed'],s),words)
                        for q in plan['pages'] for s in plan['steps']))
    assert null==res['null_maxima']
    top=max(observed,key=lambda x:x['score']);assert top==res['summary']['top']
    assert sum(v>=top['score'] for v in null)==res['summary']['null_at_least_observed']
    print('PASS 90 source cases, complete known-reading plant, 199 whole-grid shuffles, source/site parity')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();check(args.source_root)
