"""Independent full-grid LFSR, gate, control and null checker; no producer import."""
import argparse
import ast
import collections
import hashlib
import json
import pathlib
import random
import subprocess

HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
NAMES=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']
R={v:i for i,v in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path]);assert sha(b)==want,path;return b
def stream(seed,taps,n):
    reg=seed[:];out=[]
    for _ in range(n):
        out.append(reg[0]);v=sum(reg[t] for t in taps)%29;reg=reg[1:]+[v]
    return out
def ioc(x):
    n=len(x);f=collections.Counter(x)
    return 29*sum(v*(v-1) for v in f.values())/(n*(n-1)) if n>1 else 0
def score(x,words):
    s=''.join(NAMES[v] for v in x)
    return sum(s.count(w)*len(w)*len(w) for w in words)
def grid(plan,a,words,keep=True):
    rows=[];top=None
    for q in plan['pages']:
        c=a[q['source_page']];kw=q['keyword_indices']
        for d in plan['degrees']:
            seed=(kw*((d//len(kw))+1))[:d]
            for j,taps in enumerate(([1,d-1],[1,2],[2,d-1],list(range(1,d)))):
                taps=[t for t in taps if t<d]
                key=stream(seed,taps,len(c))
                for mode in plan['modes']:
                    p=[(v-k)%29 if mode=='sub' else (k-v)%29 for v,k in zip(c,key)]
                    z=ioc(p);gate=z>1.2;sc=score(p,words) if gate else None
                    row={'page':q['site_page'],'source_page':q['source_page'],'degree':d,'tap_index':j,'taps':taps,
                         'mode':mode,'ioc':z,'reported':gate,'source_score':sc,
                         'key_sha256':sha(bytes(key)),'decoded_sha256':sha(bytes(p))}
                    if keep:rows.append(row)
                    if gate and (top is None or sc+50*z>top['source_score']+50*top['ioc']):top=row
    return rows,top
def compare_rows(actual,expect):
    assert len(actual)==len(expect)
    for a,b in zip(actual,expect):
        assert a.keys()==b.keys(),(a,b)
        for k in a:
            if k=='ioc':assert abs(a[k]-b[k])<1e-14,(k,a,b)
            else:assert a[k]==b[k],(k,a,b)
def check(src):
    pb=(HERE/'plan.json').read_bytes();plan=json.loads(pb)
    ctrl=json.loads((HERE/'control-results.json').read_text(encoding='utf8'))
    res=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    assert ctrl['plan_sha256']==res['plan_sha256']==sha(pb)
    assert res['control_sha256']==sha((HERE/'control-results.json').read_bytes())
    source=blob(src,plan,plan['source_script'],plan['source_script_sha256']).decode('utf8')
    tree=ast.parse(source);words=None;source_keys=None
    for n in tree.body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id=='COMMON_3PLUS':words=ast.literal_eval(n.value)
                if isinstance(t,ast.Name) and t.id=='PAGE_KEYWORDS':source_keys=ast.literal_eval(n.value)
    assert words is not None and source_keys is not None
    a={}
    for q in plan['pages']:
        assert list(source_keys[q['source_page']][1])==q['keyword_indices']
        b=(ROOT/q['site_path']).read_bytes();assert sha(b)==q['site_sha256']
        x=[R[c] for c in json.loads(b)['raw'] if c in R]
        raw=blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8')
        assert x==[R[c] for c in raw if c in R] and len(x)==q['runes']
        a[q['source_page']]=x
    kb=(ROOT/plan['known_readings_path']).read_bytes();assert sha(kb)==plan['known_readings_sha256']
    p=next(z for z in json.loads(kb)['controls'] if z['id']==plan['control']['reading'])['decoded_pages'][0]['rune_indices']
    q=plan['pages'][0];d=plan['control']['degree'];kw=q['keyword_indices'];seed=(kw*((d//len(kw))+1))[:d]
    k=stream(seed,[1,d-1],len(p));c=[(v+z)%29 for v,z in zip(p,k)]
    synthetic={q['source_page']:c};rng=random.Random(plan['control']['seed'])
    for other in plan['pages'][1:]:synthetic[other['source_page']]=[rng.randrange(29) for _ in range(other['runes'])]
    crow,ctop=grid(plan,synthetic,words)
    target=next(z for z in crow if z['source_page']==q['source_page'] and z['degree']==d and z['tap_index']==0 and z['mode']=='sub')
    assert [(v-z)%29 for v,z in zip(c,k)]==p and target==ctop and target['reported']
    power={'reading':plan['control']['reading'],'length':len(p),'cipher_sha256':sha(bytes(c)),
           'plain_sha256':sha(bytes(p)),'true_case':target,'top':ctop,'reported_cases':sum(z['reported'] for z in crow),
           'whole_grid_cases':len(crow),'exact_recovery':True}
    assert ctrl['control']==res['control']==power
    rows,top=grid(plan,a,words);compare_rows(rows,res['observed'])
    assert top==res['summary']['top'] and len(rows)==400
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=a[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        _,winner=grid(plan,shuffled,words,keep=False)
        null.append(None if winner is None else {'score':winner['source_score']+50*winner['ioc'],'reported':True})
    assert len(null)==199 and len(res['null_maxima'])==199
    for a,b in zip(null,res['null_maxima']):
        assert a is None and b is None or (a is not None and b is not None and a['reported']==b['reported'] and abs(a['score']-b['score'])<1e-14)
    assert res['summary']['reported']==sum(z['reported'] for z in rows)
    assert res['summary']['null_reported_trials']==sum(z is not None for z in null)
    print('PASS source/site parity, 400 cases, complete 209-rune control, 199 whole-grid shuffles')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();check(args.source_root)
