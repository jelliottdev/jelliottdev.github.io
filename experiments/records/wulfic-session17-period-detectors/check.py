"""Independent lag-pair and column-pair check of both bounded detectors."""
import argparse,ast,collections,hashlib,json,pathlib,random,subprocess
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
DEFAULT=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ';R={c:i for i,c in enumerate(RUNES)}
def sha(b):return hashlib.sha256(b).hexdigest()
def source_blob(src,plan,path,want):
    b=subprocess.check_output(['git','-C',str(src),'show',plan['source_revision']+':'+path]);assert sha(b)==want;return b
def encoded(text):
    pairs={'TH':2,'EO':12,'NG':21,'EA':28,'AE':25,'IA':27,'OE':22}
    singles=dict(zip('FUVORCKGWHNIJPXSTBEMLDAY',[0,1,1,3,4,5,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,23,24,26]))
    s=text.upper();ans=[];i=0
    while i<len(s):
        pair=s[i:i+2]
        if pair in pairs:ans.append(pairs[pair]);i+=2
        else:
            if s[i] in singles:ans.append(singles[s[i]])
            i+=1
    return ans
def rows_from_source(src,plan):
    tree=ast.parse(source_blob(src,plan,plan['source_script'],plan['source_script_sha256']).decode('utf8'))
    f=next(z for z in tree.body if isinstance(z,ast.FunctionDef) and z.name=='test8_known_plaintext_attack')
    candidates=next(ast.literal_eval(z.value) for z in ast.walk(f) if isinstance(z,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='LP_KNOWN_TEXTS' for t in z.targets))
    texts={}
    for q in plan['test8_candidates']:
        raw=candidates[q['name']];v=encoded(raw)
        assert sha(raw.encode('utf8'))==q['source_text_sha256'] and len(v)==q['gp_length'] and sha(bytes(v))==q['gp_sha256']
        texts[q['name']]=v
    pages={}
    for q in plan['pages']:
        raw=source_blob(src,plan,q['source_path'],q['source_sha256']).decode('utf8')
        stream=[]
        for line in raw.splitlines():
            alpha=sum(c.isascii() and c.isalpha() for c in line);runes=sum(c in R for c in line)
            if alpha>0 and runes==0 or alpha>2 and runes<alpha:continue
            stream.extend(R[c] for c in line if c in R)
        sb=(ROOT/q['site_path']).read_bytes();assert sha(sb)==q['site_sha256']
        assert stream==[R[c] for c in json.loads(sb)['raw'] if c in R] and len(stream)==q['rune_count']
        pages[q['source_page']]=stream
    return texts,pages
def test8(plan,pages,texts,detail=True):
    reported=[];best=None;count_grid=0
    for page in plan['test8_source_pages']:
        c=pages[page];n=len(c)
        if n<30:continue
        for name,v in texts.items():
            if len(v)<20:continue
            step=max(1,n//20)
            for off in range(0,min(len(v)+n,2000),step):
                count_grid+=1
                # Compare modular differences at paired positions directly; no
                # inferred-key stream or producer lag-score routine is used.
                for lag in plan['test8_periods']:
                    if lag>=n//2:break
                    hits=sum(((c[i]-v[(off+i)%len(v)])-(c[i+lag]-v[(off+i+lag)%len(v)]))%29==0
                             for i in range(n-lag))
                    den=n-lag
                    if lag==plan['test8_periods'][0]:best_hits_num=hits;best_hits_den=den;win=lag
                    elif hits*best_hits_den>best_hits_num*den:best_hits_num=hits;best_hits_den=den;win=lag
                row={'source_page':page,'candidate':name,'offset':off,'period':win,
                     'equal_pairs':best_hits_num,'opportunities':best_hits_den,'match_fraction':best_hits_num/best_hits_den}
                if best is None or best_hits_num*best['opportunities']>best['equal_pairs']*best_hits_den:best=row
                if detail and best_hits_num*4>best_hits_den:reported.append(row)
    return {'settings_including_equivalent_signs':2*count_grid,'unique_lag_grids':count_grid,
            'reported_pair_count':2*len(reported) if detail else None,
            'reported_unique':reported if detail else None,'top':best}
def stream_ioc(x):
    n=len(x)
    if n<2:return 0.0
    matches=sum(x[i]==x[j] for i in range(n) for j in range(i+1,n))
    return 29*2*matches/(n*(n-1))
def split_ioc(c,p):
    parts=[c[j::p] for j in range(p)]
    return sum(stream_ioc(v) for v in parts if len(v)>1)/sum(len(v)>1 for v in parts)
def k_factors(c,primes):
    seen={};ds=[]
    for i in range(len(c)-3):
        t=tuple(c[i:i+3]);ds.append(i-seen[t]) if t in seen else seen.setdefault(t,i)
    counts=collections.Counter()
    for d in ds:
        for p in primes:
            if d%p==0:counts[p]+=1
    return [[p,v] for v,p in sorted(((v,p) for p,v in counts.items()),reverse=True)[:5]]
def test9(plan,pages,detail=True):
    page_rows=[];flagged=[];globaltop=None
    for page in plan['test9_source_pages']:
        c=pages[page]
        if len(c)<50:continue
        baseline=stream_ioc(c);periods=[]
        for p in plan['test9_periods']:
            if p>len(c)//3:break
            val=split_ioc(c,p)
            row={'source_page':page,'period':p,'split_ioc':val,'baseline_ioc':baseline,'ratio':val/baseline if baseline else None}
            periods.append(row)
            if globaltop is None or row['ratio']>globaltop['ratio']:globaltop=row
        ranked=sorted(periods,key=lambda z:(z['split_ioc'],z['period']),reverse=True)
        winner=ranked[0]
        flag=winner['split_ioc']>baseline*1.3
        if flag:flagged.append({'source_page':page,'period':winner['period'],'ratio':winner['ratio']})
        if detail:page_rows.append({'source_page':page,'rune_count':len(c),'baseline_ioc':baseline,
              'periods':periods,'source_top_five_periods':[z['period'] for z in ranked[:5]],
              'kasiski_prime_factors':k_factors(c,plan['test9_periods']),
              'flagged_period':winner['period'] if flag else None})
    return {'pages':page_rows if detail else None,'flagged':flagged if detail else None,
            'flag_count':len(flagged),'global_top_ratio':globaltop}
def eq(a,b):
    if isinstance(a,float) and isinstance(b,float):return abs(a-b)<1e-12
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(eq(x,y) for x,y in zip(a,b))
    if isinstance(a,dict) and isinstance(b,dict):return a.keys()==b.keys() and all(eq(a[k],b[k]) for k in a)
    return a==b
def check(src):
    pb=(H/'plan.json').read_bytes();plan=json.loads(pb)
    ctrl=json.loads((H/'control-results.json').read_text(encoding='utf8'))
    res=json.loads((H/'results.json').read_text(encoding='utf8'))
    assert ctrl['plan_sha256']==res['plan_sha256']==sha(pb)
    assert res['control_sha256']==sha((H/'control-results.json').read_bytes())
    texts,pages=rows_from_source(src,plan)
    q=plan['control'];pg=q['source_page_slot'];pt=texts[q['candidate']];n=len(pages[pg]);off=q['candidate_offset'];key=q['key_values'];d=q['key_period']
    plain=[pt[(off+i)%len(pt)] for i in range(n)];cipher=[(v+key[i%d])%29 for i,v in enumerate(plain)]
    assert sha(bytes(plain))==ctrl['control']['plaintext_sha256'] and sha(bytes(cipher))==ctrl['control']['cipher_sha256']
    rng=random.Random(q['seed']);synthetic={k:[rng.randrange(29) for _ in v] for k,v in pages.items()};synthetic[pg]=cipher
    ca=test8(plan,synthetic,texts);cb=test9(plan,synthetic)
    expected=ctrl['control']
    assert any(z['source_page']==pg and z['candidate']==q['candidate'] and z['offset']==off and z['period']==d for z in ca['reported_unique'])
    assert any(z['source_page']==pg and z['period']==d for z in cb['flagged'])
    assert eq(ca['top'],expected['test8_global_top']) and eq(cb['global_top_ratio'],expected['test9_global_top'])
    a=test8(plan,pages,texts);b=test9(plan,pages)
    assert eq(a,res['test8']),'Test8 source-derived rows differ'
    assert eq(b,res['test9']),'Test9 source-derived rows differ'
    rng=random.Random(plan['null']['seed']);null=[]
    for _ in range(plan['null']['trials']):
        shuffled={}
        for q in plan['pages']:
            x=pages[q['source_page']][:];rng.shuffle(x);shuffled[q['source_page']]=x
        aa=test8(plan,shuffled,texts,detail=False);bb=test9(plan,shuffled,detail=False)
        null.append({'test8_top':aa['top'],'test9_top_ratio':bb['global_top_ratio'],'test9_flag_count':bb['flag_count']})
    assert eq(null,res['null_maxima'])
    print('PASS Test8/9 source data, independent lag/column pairs, planted period and 49 shared full searches')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=DEFAULT);args=ap.parse_args();check(args.source_root)
