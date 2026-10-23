"""Independent byte/input, selector, control and complete-null checker."""
import argparse,ast,collections,hashlib,json,pathlib,random,subprocess
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ';R={c:i for i,c in enumerate(RUNES)}
NAMES=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']
MAP={v:i for i,v in enumerate(NAMES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path]);assert sha(b)==want,path;return b
def encode(t):
    t=t.upper();out=[];i=0
    while i<len(t):
        x=t[i:i+2]
        if x in MAP:out.append(MAP[x]);i+=2;continue
        if t[i:i+3]=='ING':out.append(MAP['NG']);i+=3;continue
        ch={'K':'C','V':'U','Q':'C'}.get(t[i],t[i]);i+=1
        if ch in MAP:out.append(MAP[ch])
    return out
def ioc(x):
    n=len(x);f=collections.Counter(x)
    return 29*sum(z*(z-1) for z in f.values())/(n*(n-1)) if n>1 else 0
def dec(c,k,mode):
    if mode=='sub':return [(v-z)%29 for v,z in zip(c,k)]
    if mode=='add':return [(v+z)%29 for v,z in zip(c,k)]
    return [(z-v)%29 for v,z in zip(c,k)]
def score(x,content,words):
    text=''.join(NAMES[z] for z in x)
    s1=sum(text.count(w)*len(w)**2 for w in words)
    shaped=[];part=[];idx=0
    for ch in content:
        if ch in R:
            if idx<len(x):part.append(NAMES[x[idx]])
            idx+=1
        elif ch in '-.':
            if part:shaped.append(''.join(part));part=[]
    if part:shaped.append(''.join(part))
    s2=0;match=0
    for w in shaped:
        if w in words:s2+=len(w)*10;match+=1
        elif w.replace('C','K') in words or w.replace('U','V') in words:s2+=len(w)*8;match+=1
    return s1,s2,match,len(shaped)
def select(c,layout,key,name,page,words):
    n=len(c);lim=len(key)-n;off=-1;best=0;mode0=None;coarse=0;fine=0
    for j in range(0,lim,100):
        segment=key[j:j+n]
        for mode in ('sub','add','beaufort'):
            z=ioc(dec(c,segment,mode));coarse+=1
            if z>best:off=j;best=z;mode0=mode
    if off<0:return None
    for j in range(max(0,off-100),min(lim,off+100)):
        z=ioc(dec(c,key[j:j+n],mode0));fine+=1
        if z>best:off=j;best=z
    p=dec(c,key[off:off+n],mode0);s1,s2,m,total=score(p,layout,words)
    return {'page':page,'key':name,'offset':off,'mode':mode0,'ioc':best,
            'source_score':s1+s2,'substring_score':s1,'structure_score':s2,
            'matched_words':m,'words':total,'decoded_sha256':sha(bytes(p)),
            'coarse_cases':coarse,'refined_cases':fine,'key_length':len(key)}
def compare(a,b):
    assert a.keys()==b.keys(),(a,b)
    for k in a:
        if k=='ioc':assert abs(a[k]-b[k])<1e-14,(k,a,b)
        else:assert a[k]==b[k],(k,a,b)
def best(rows):return max(rows,key=lambda x:x['source_score']+50*x['ioc'])
def check(src):
    pb=(H/'plan.json').read_bytes();plan=json.loads(pb)
    ctrl=json.loads((H/'control-results.json').read_text(encoding='utf8'))
    res=json.loads((H/'results.json').read_text(encoding='utf8'))
    assert ctrl['plan_sha256']==res['plan_sha256']==sha(pb)
    assert res['control_sha256']==sha((H/'control-results.json').read_bytes())
    program=blob(src,plan,plan['source_script'],plan['source_script_sha256']).decode('utf8');tree=ast.parse(program)
    words=None;knowntexts=None
    for node in tree.body:
        if isinstance(node,ast.Assign):
            for t in node.targets:
                if isinstance(t,ast.Name) and t.id=='COMMON_3PLUS':words=ast.literal_eval(node.value)
        if isinstance(node,ast.FunctionDef) and node.name=='load_solved_plaintext':
            for child in ast.walk(node):
                if isinstance(child,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='known_texts' for t in child.targets):
                    knowntexts=ast.literal_eval(child.value)
    assert words is not None and knowntexts is not None
    keys={};a={};layouts={}
    for q in plan['corpora']:
        raw=' '.join(knowntexts) if q['name']=='SolvedLP' else blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8',errors='ignore')
        keys[q['name']]=encode(raw)
    for q in plan['pages']:
        raw=blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8')
        sb=(ROOT/q['site_path']).read_bytes();assert sha(sb)==q['site_sha256']
        x=[R[c] for c in raw if c in R];assert x==[R[c] for c in json.loads(sb)['raw'] if c in R]
        a[q['source_page']]=x;layouts[q['source_page']]=raw
    kb=(ROOT/plan['known_readings_path']).read_bytes();assert sha(kb)==plan['known_readings_sha256']
    p=next(z for z in json.loads(kb)['controls'] if z['id']==plan['control']['reading'])['decoded_pages'][0]['rune_indices']
    lb=(ROOT/plan['control_layout_path']).read_bytes();assert sha(lb)==plan['control_layout_sha256'];layout=json.loads(lb)['raw']
    assert ctrl['control']['plain_sha256']==sha(bytes(p)) and ctrl['control']['length']==len(p)
    assert ctrl['control']['key_lengths']=={n:len(v) for n,v in keys.items()}
    assert ctrl['control']['key_sha256']=={n:sha(bytes(v)) for n,v in keys.items()}
    slot=plan['control']['true_page_slot'];n=len(p)
    for row in ctrl['control']['one_page']:
        name=row['key'];off=row['planted_offset'];key=keys[name]
        c=[(v+z)%29 for v,z in zip(p,key[off:off+n])]
        assert sha(bytes(c))==row['cipher_sha256']
        got=select(c,layout,key,name,slot,words);compare(got,row['selected'])
        assert row['full_recovery']==(dec(c,key[got['offset']:got['offset']+n],got['mode'])==p)
    assert all(z['full_recovery'] for z in ctrl['control']['one_page'] if z['kind']=='on_grid')
    rng=random.Random(plan['control']['seed']);synthetic={};slayout={}
    for q in plan['pages']:
        page=q['source_page'];synthetic[page]=[rng.randrange(29) for _ in range(q['runes'])];slayout[page]=layouts[page]
    off=plan['control']['on_grid_offset'];synthetic[slot]=[(v+z)%29 for v,z in zip(p,keys['LiberAL'][off:off+n])];slayout[slot]=layout
    whole=[select(synthetic[q['source_page']],slayout[q['source_page']],key,name,q['source_page'],words)
           for q in plan['pages'] for name,key in keys.items()]
    champion=best(whole);compare(champion,ctrl['control']['whole_grid']['true_case'])
    assert champion['page']==slot and champion['key']=='LiberAL' and champion['offset']==off and ctrl['control']['whole_grid']['rank']==1
    observed=[select(a[q['source_page']],layouts[q['source_page']],key,name,q['source_page'],words)
              for q in plan['pages'] for name,key in keys.items()]
    assert len(observed)==len(res['observed'])==72
    for x,y in zip(observed,res['observed']):compare(x,y)
    compare(best(observed),res['summary']['top'])
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=a[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        rows=[select(shuffled[q['source_page']],layouts[q['source_page']],key,name,q['source_page'],words)
              for q in plan['pages'] for name,key in keys.items()]
        winner=best(rows);null.append({'source_score':winner['source_score'],'ioc':winner['ioc'],
                                        'ranking_score':winner['source_score']+50*winner['ioc']})
    assert len(null)==len(res['null_maxima'])==49
    for x,y in zip(null,res['null_maxima']):
        assert x['source_score']==y['source_score'] and abs(x['ioc']-y['ioc'])<1e-14 and abs(x['ranking_score']-y['ranking_score'])<1e-12
    top=best(observed);score0=top['source_score']+50*top['ioc']
    assert res['summary']['null_at_least_observed']==sum(x['ranking_score']>=score0 for x in null)
    print('PASS source input identity, four-key plants, 72 target winners, 49 full-grid shuffles')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();check(args.source_root)
