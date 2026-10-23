"""Exact bounded Test8/9 period statistics from pinned Wulfic session17 source."""
import argparse,ast,collections,hashlib,json,math,pathlib,random,subprocess,time
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ';R={c:i for i,c in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path]);assert sha(b)==want,path;return b
def assigned(fn,name):
    rows=[ast.literal_eval(node.value) for node in ast.walk(fn) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets)]
    assert len(rows)==1,name;return rows[0]
def digraph(text):
    t=text.upper();i=0;out=[]
    doubles={'TH':2,'EO':12,'NG':21,'EA':28,'AE':25,'IA':27,'OE':22}
    singles={'F':0,'U':1,'V':1,'O':3,'R':4,'C':5,'K':5,'G':6,'W':7,'H':8,'N':9,'I':10,'J':11,'P':13,'X':14,'S':15,'T':16,'B':17,'E':18,'M':19,'L':20,'D':23,'A':24,'Y':26}
    while i<len(t):
        if t[i:i+2] in doubles:out.append(doubles[t[i:i+2]]);i+=2
        else:
            if t[i] in singles:out.append(singles[t[i]])
            i+=1
    return out
def parse_source(raw):
    out=[]
    for line in raw.splitlines():
        ascii_alpha=sum(c.isascii() and c.isalpha() for c in line)
        rune_count=sum(c in R for c in line)
        if ascii_alpha>0 and rune_count==0 or ascii_alpha>2 and rune_count<ascii_alpha:continue
        out.extend(R[c] for c in line if c in R)
    return out
def inputs(src,plan):
    source=blob(src,plan,plan['source_script'],plan['source_script_sha256']).decode('utf8')
    tree=ast.parse(source)
    f8=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='test8_known_plaintext_attack')
    f9=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='test9_kasiski_ioc')
    originals=assigned(f8,'LP_KNOWN_TEXTS')
    assert list(originals)==[z['name'] for z in plan['test8_candidates']]
    assert assigned(f8,'primes_to_test')==plan['test8_periods'] and assigned(f9,'PRIMES_TO_TEST')==plan['test9_periods']
    texts={}
    for q in plan['test8_candidates']:
        txt=originals[q['name']];v=digraph(txt)
        assert sha(txt.encode('utf8'))==q['source_text_sha256'] and len(v)==q['gp_length'] and sha(bytes(v))==q['gp_sha256']
        texts[q['name']]=v
    pages={}
    for q in plan['pages']:
        raw=blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8');x=parse_source(raw)
        sb=(ROOT/q['site_path']).read_bytes();assert sha(sb)==q['site_sha256']
        assert x==[R[c] for c in json.loads(sb)['raw'] if c in R] and len(x)==q['rune_count']
        pages[q['source_page']]=x
    return texts,pages
def lag_best(key,periods):
    n=len(key);best_count=0;best_den=1;best_p=0
    for p in periods:
        if p>=n//2:break
        den=n-p;count=sum(a==b for a,b in zip(key,key[p:]))
        if count*best_den>best_count*den:best_count=count;best_den=den;best_p=p
    return best_count,best_den,best_p
def test8(plan,pages,texts,retain=True):
    reports=[];best=None;settings=0
    for page in plan['test8_source_pages']:
        cipher=pages[page];n=len(cipher)
        if n<30:continue
        for name,pt in texts.items():
            if len(pt)<20:continue
            step=max(1,n//20)
            for off in range(0,min(len(pt)+n,2000),step):
                aligned=[pt[(off+i)%len(pt)] for i in range(n)]
                key=[(c-v)%29 for c,v in zip(cipher,aligned)]
                count,den,period=lag_best(key,plan['test8_periods']);settings+=2
                row={'source_page':page,'candidate':name,'offset':off,'period':period,
                     'equal_pairs':count,'opportunities':den,'match_fraction':count/den if period else 0}
                if best is None or count*best['opportunities']>best['equal_pairs']*den:best=row
                if period and 4*count>den and retain:reports.append(row)
    return {'settings_including_equivalent_signs':settings,'unique_lag_grids':settings//2,
            'reported_pair_count':2*len(reports) if retain else None,
            'reported_unique':reports if retain else None,'top':best}
def ioc(seq):
    n=len(seq);f=collections.Counter(seq)
    return 29*sum(v*(v-1) for v in f.values())/(n*(n-1)) if n>1 else 0.0
def kasiski(cipher):
    seen={};distances=[]
    for i in range(len(cipher)-3):
        gram=tuple(cipher[i:i+3])
        if gram in seen:distances.append(i-seen[gram])
        else:seen[gram]=i
    out=collections.Counter()
    for d in distances:
        for fac in range(2,d+1):
            if d%fac==0:out[fac]+=1
    return out
def test9(plan,pages,retain=True):
    allrows=[];globaltop=None;flagged=[]
    for page in plan['test9_source_pages']:
        c=pages[page]
        if len(c)<50:continue
        base=ioc(c);rows=[]
        for p in plan['test9_periods']:
            if p>len(c)//3:break
            chunks=[c[i::p] for i in range(p)]
            score=sum(ioc(s) for s in chunks if len(s)>1)/sum(len(s)>1 for s in chunks)
            z={'source_page':page,'period':p,'split_ioc':score,'baseline_ioc':base,'ratio':score/base if base else None}
            rows.append(z)
            if globaltop is None or z['ratio']>globaltop['ratio']:globaltop=z
        ranked=sorted(rows,key=lambda z:(z['split_ioc'],z['period']),reverse=True)
        winner=ranked[0] if ranked else None
        if winner is not None and winner['split_ioc']>base*1.3:flagged.append({'source_page':page,'period':winner['period'],'ratio':winner['ratio']})
        if retain:
            counts=kasiski(c)
            # Source prints prime GCD factors of first-repeat trigram distances.
            topg=sorted(((v,p) for p,v in counts.items() if p in plan['test9_periods']),reverse=True)[:5]
            allrows.append({'source_page':page,'rune_count':len(c),'baseline_ioc':base,'periods':rows,
                            'source_top_five_periods':[z['period'] for z in ranked[:5]],
                            'kasiski_prime_factors':[[p,v] for v,p in topg],
                            'flagged_period':winner['period'] if winner is not None and winner['split_ioc']>base*1.3 else None})
    return {'pages':allrows if retain else None,'flagged':flagged if retain else None,
            'flag_count':len(flagged),'global_top_ratio':globaltop}
def control(plan,texts,pages):
    q=plan['control'];page=q['source_page_slot'];n=len(pages[page]);v=texts[q['candidate']];off=q['candidate_offset'];key=q['key_values'];period=q['key_period']
    plain=[v[(off+i)%len(v)] for i in range(n)];cipher=[(x+key[i%period])%29 for i,x in enumerate(plain)]
    assert len(key)==period and len(set(key))>1
    rng=random.Random(q['seed']);synthetic={p:[rng.randrange(29) for _ in a] for p,a in pages.items()};synthetic[page]=cipher
    a=test8(plan,synthetic,texts);b=test9(plan,synthetic)
    matches=[z for z in a['reported_unique'] if z['source_page']==page and z['candidate']==q['candidate'] and z['offset']==off and z['period']==period]
    flagged=[z for z in b['flagged'] if z['source_page']==page and z['period']==period]
    assert matches and flagged,(matches,flagged,b['pages'][0]['source_top_five_periods'])
    # The chosen candidate and period identify the exact full planted plaintext/key in Test8.
    recovered=[(cipher[i]-key[i%period])%29 for i in range(n)]==plain
    assert recovered
    return {'cipher_sha256':sha(bytes(cipher)),'plaintext_sha256':sha(bytes(plain)),
            'test8_matching_row':matches[0],'test8_global_top':a['top'],
            'test8_reported_unique':len(a['reported_unique']),
            'test9_flagged_page':flagged[0],'test9_global_top':b['global_top_ratio'],
            'test9_flag_count':b['flag_count'],'exact_generated_plaintext_recovery':recovered,
            'key_sha256':sha(bytes(key))}
def compute(src,control_only=False):
    pb=(H/'plan.json').read_bytes();plan=json.loads(pb);texts,pages=inputs(src,plan)
    planted=control(plan,texts,pages)
    if control_only:return {'schema':'wulfic-session17-period-control-v1','plan_sha256':sha(pb),'control':planted}
    a=test8(plan,pages,texts);b=test9(plan,pages)
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=pages[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        aa=test8(plan,shuffled,texts,retain=False);bb=test9(plan,shuffled,retain=False)
        null.append({'test8_top':aa['top'],'test9_top_ratio':bb['global_top_ratio'],
                     'test9_flag_count':bb['flag_count']})
    at=a['top']['match_fraction'];bt=b['global_top_ratio']['ratio']
    return {'schema':'wulfic-session17-period-results-v1','plan_sha256':sha(pb),
            'control_sha256':sha((H/'control-results.json').read_bytes()),
            'test8':a,'test9':b,'null_maxima':null,
            'summary':{'test8_unique_lag_grids':a['unique_lag_grids'],'test8_reported_unique':len(a['reported_unique']),
                       'test8_top':a['top'],'test8_null_at_least':sum(z['test8_top']['match_fraction']>=at for z in null),
                       'test9_flagged_pages':b['flag_count'],'test9_top':b['global_top_ratio'],
                       'test9_null_at_least':sum(z['test9_top_ratio']['ratio']>=bt for z in null),
                       'null_trials':len(null)}}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT)
    ap.add_argument('--control-only',action='store_true');ap.add_argument('--check',action='store_true');args=ap.parse_args()
    result=compute(args.source_root,args.control_only);path=H/('control-results.json' if args.control_only else 'results.json')
    s=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.check:assert path.read_text(encoding='utf8')==s;print('PASS',path.name)
    else:path.write_text(s,encoding='utf8',newline='\n');print(json.dumps(result.get('summary',result.get('control'))))
