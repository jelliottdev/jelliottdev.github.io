"""Exact method-5 selector from pinned Wulfic advanced solver, in isolation."""
import argparse,hashlib,importlib.util,json,pathlib,random,subprocess,tempfile
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ';R={c:i for i,c in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path]);assert sha(b)==want,path;return b
def source(src,plan):
    b=blob(src,plan,plan['source_script'],plan['source_script_sha256'])
    with tempfile.TemporaryDirectory() as d:
        p=pathlib.Path(d)/'source.py';p.write_bytes(b)
        spec=importlib.util.spec_from_file_location('source',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def inputs(src,plan):
    m=source(src,plan);keys={};pages={};content={}
    for q in plan['corpora']:
        if q['name']=='SolvedLP':x=m.load_solved_plaintext()
        else:
            b=blob(src,plan,q['source_path'],q['source_sha256'])
            x=m.text_to_gp_indices(b.decode('utf8',errors='ignore'))
        keys[q['name']]=x
    for q in plan['pages']:
        raw=blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8')
        sb=(ROOT/q['site_path']).read_bytes();assert sha(sb)==q['site_sha256']
        site=json.loads(sb);a=[R[c] for c in raw if c in R]
        assert a==[R[c] for c in site['raw'] if c in R] and len(a)==q['runes']
        pages[q['source_page']]=a;content[q['source_page']]=raw
    kb=(ROOT/plan['known_readings_path']).read_bytes();assert sha(kb)==plan['known_readings_sha256']
    known=json.loads(kb);p=next(z for z in known['controls'] if z['id']==plan['control']['reading'])['decoded_pages'][0]['rune_indices']
    lb=(ROOT/plan['control_layout_path']).read_bytes();assert sha(lb)==plan['control_layout_sha256']
    layout=json.loads(lb)['raw'];assert len([v for v in layout if v in R])==len(p)
    return m,keys,pages,content,p,layout
def select(m,cipher,content,key,name,page,keep_counts=True):
    n=len(cipher);limit=len(key)-n;best_offset=-1;best_ioc=0;best_mode=None
    coarse=0;refine=0
    for off in range(0,limit,100):
        segment=key[off:off+n]
        for mode in ('sub','add','beaufort'):
            plain=m.running_key_decrypt(cipher,segment,mode);z=m.compute_ioc(plain);coarse+=1
            if z>best_ioc:best_ioc=z;best_offset=off;best_mode=mode
    if best_offset<0:return None
    for off in range(max(0,best_offset-100),min(limit,best_offset+100)):
        plain=m.running_key_decrypt(cipher,key[off:off+n],best_mode);z=m.compute_ioc(plain);refine+=1
        if z>best_ioc:best_ioc=z;best_offset=off
    plain=m.running_key_decrypt(cipher,key[best_offset:best_offset+n],best_mode)
    text=m.to_runeglish(plain);sc=m.score_text(text)
    struct,matched,total,_=m.score_with_structure(content,plain,None)
    return {'page':page,'key':name,'offset':best_offset,'mode':best_mode,'ioc':best_ioc,
            'source_score':sc+struct,'substring_score':sc,'structure_score':struct,
            'matched_words':matched,'words':total,'decoded_sha256':sha(bytes(plain)),
            'coarse_cases':coarse,'refined_cases':refine,'key_length':len(key)}
def best(rows):
    return max(rows,key=lambda x:x['source_score']+50*x['ioc'])
def controls(plan,m,keys,pages,content,p,layout):
    out=[];slot=plan['control']['true_page_slot'];n=len(p)
    for name,key in keys.items():
        for kind,off in (('on_grid',plan['control']['on_grid_offset']),('off_grid',plan['control']['off_grid_offset'])):
            c=[(v+k)%29 for v,k in zip(p,key[off:off+n])]
            row=select(m,c,layout,key,name,slot)
            recovered=m.running_key_decrypt(c,key[row['offset']:row['offset']+n],row['mode'])==p
            out.append({'key':name,'kind':kind,'planted_offset':off,'cipher_sha256':sha(bytes(c)),
                        'full_recovery':recovered,'selected':row})
    assert all(z['full_recovery'] and z['selected']['offset']==z['planted_offset'] and z['selected']['mode']=='sub' for z in out if z['kind']=='on_grid')
    rng=random.Random(plan['control']['seed']);synthetic={};layouts={}
    for q in plan['pages']:
        page=q['source_page'];layouts[page]=content[page]
        synthetic[page]=[rng.randrange(29) for _ in range(q['runes'])]
    off=plan['control']['on_grid_offset'];key=keys['LiberAL'];synthetic[slot]=[(v+k)%29 for v,k in zip(p,key[off:off+n])];layouts[slot]=layout
    rows=[select(m,synthetic[q['source_page']],layouts[q['source_page']],key,name,q['source_page'])
          for q in plan['pages'] for name,key in keys.items()]
    champion=best(rows);assert champion['page']==slot and champion['key']=='LiberAL' and champion['offset']==off and champion['mode']=='sub'
    assert m.running_key_decrypt(synthetic[slot],keys['LiberAL'][off:off+n],'sub')==p
    return {'one_page':out,'whole_grid':{'case_count':len(rows),'true_case':champion,
             'rank':1+sum(z['source_score']+50*z['ioc']>champion['source_score']+50*champion['ioc'] for z in rows),
             'full_recovery':True,'synthetic_seed':plan['control']['seed']},
            'plain_sha256':sha(bytes(p)),'length':n,
            'key_lengths':{name:len(key) for name,key in keys.items()},
            'key_sha256':{name:sha(bytes(key)) for name,key in keys.items()}}
def compute(src,control_only=False):
    pb=(H/'plan.json').read_bytes();plan=json.loads(pb);m,keys,pages,content,p,layout=inputs(src,plan)
    power=controls(plan,m,keys,pages,content,p,layout)
    if control_only:return {'schema':'wulfic-advanced-running-keys-control-v1','plan_sha256':sha(pb),'control':power}
    observed=[select(m,pages[q['source_page']],content[q['source_page']],key,name,q['source_page'])
              for q in plan['pages'] for name,key in keys.items()]
    top=best(observed);score=top['source_score']+50*top['ioc']
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=pages[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        rows=[select(m,shuffled[q['source_page']],content[q['source_page']],key,name,q['source_page'])
              for q in plan['pages'] for name,key in keys.items()]
        b=best(rows);null.append({'source_score':b['source_score'],'ioc':b['ioc'],'ranking_score':b['source_score']+50*b['ioc']})
    return {'schema':'wulfic-advanced-running-keys-results-v1','plan_sha256':sha(pb),
            'control_sha256':sha((H/'control-results.json').read_bytes()),'observed':observed,'null_maxima':null,
            'summary':{'cases':len(observed),'top':top,'top_ranking_score':score,'null_trials':len(null),
                       'null_at_least_observed':sum(x['ranking_score']>=score for x in null)}}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT)
    ap.add_argument('--control-only',action='store_true');ap.add_argument('--check',action='store_true');a=ap.parse_args()
    result=compute(a.source_root,a.control_only);path=H/('control-results.json' if a.control_only else 'results.json')
    s=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if a.check:assert path.read_text(encoding='utf8')==s;print('PASS',path.name)
    else:path.write_text(s,encoding='utf8',newline='\n');print(json.dumps(result.get('summary',result.get('control'))))
