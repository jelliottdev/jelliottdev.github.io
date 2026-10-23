"""Pinned source replay plus a separately labeled held-out word-vote diagnostic."""
from __future__ import annotations
import argparse, ast, contextlib, hashlib, io, json, random, subprocess, tempfile
from collections import defaultdict, Counter
from pathlib import Path
P=Path(__file__).resolve().parent
ROOT=P.parents[2]
def sha(b): return hashlib.sha256(b).hexdigest()
def load_source(repo,plan):
    spec=f"{plan['source_revision']}:{plan['primary_source']['path']}"
    blob=subprocess.check_output(['git','rev-parse',spec],cwd=repo,text=True).strip()
    assert blob==plan['primary_source']['git_blob']
    raw=subprocess.check_output(['git','show',spec],cwd=repo)
    tree=ast.parse(raw.decode('utf-8'))
    tree.body=[n for n in tree.body if not isinstance(n,ast.If) or not (isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='__name__')]
    ns={'__name__':'pinned_period_solver','__file__':'placeholder'}
    exec(compile(tree,'<pinned-source>','exec'),ns)
    return ns,sha(raw)
def source_page(repo,plan,target):
    b=subprocess.check_output(['git','show',f"{plan['source_revision']}:{target['source_file']}"],cwd=repo)
    site=ROOT/'data'/'pages'/f"{target['current_page']}.json"
    raw=json.loads(site.read_text(encoding='utf-8'))['raw'].encode('utf-8')
    assert b.strip()==raw.strip(),target
    return b,site
def voted_key(cipher,words,period,mode,dictionary):
    votes=[{} for _ in range(period)]
    attempted=0
    for start,word in words:
        L=len(word)
        if not 2<=L<=15: continue
        for name,crib in dictionary.get(L,[]):
            derived={}
            for j,(c,p) in enumerate(zip(word,crib)):
                pos=(start+j)%period
                key=(c-p)%29 if mode=='SUB' else (p-c)%29 if mode=='ADD' else (p+c)%29
                if pos in derived and derived[pos]!=key: break
                derived[pos]=key
            else:
                attempted+=1
                for pos,key in derived.items(): votes[pos][key]=votes[pos].get(key,0)+1
    # Python dict insertion order reproduces the archived max() tie rule.
    key=[max(v,key=v.get) if v else 0 for v in votes]
    conf=[max(v.values())/sum(v.values()) if v else 0 for v in votes]
    return key,conf,attempted
def apply(cipher,key,mode):
    if mode=='SUB':return [(c-key[i%len(key)])%29 for i,c in enumerate(cipher)]
    if mode=='ADD':return [(c+key[i%len(key)])%29 for i,c in enumerate(cipher)]
    return [(key[i%len(key)]-c)%29 for i,c in enumerate(cipher)]
def heldout(cipher,words,period,mode,dictionary,wordset,train_parity):
    train=[x for i,x in enumerate(words) if i%2==train_parity]
    test=[x for i,x in enumerate(words) if i%2!=train_parity and 2<=len(x[1])<=15]
    key,conf,attempted=voted_key(cipher,train,period,mode,dictionary)
    dec=apply(cipher,key,mode)
    hits=sum(tuple(dec[start:start+len(w)]) in wordset for start,w in test)
    return {'hits':hits,'eligible':len(test),'rate':hits/len(test) if test else 0,'key_sha256':sha(bytes(key)),'vote_cribs':attempted}
def plant(cipher,words,period,mode,dictionary,seed):
    rng=random.Random(seed); plain=[rng.randrange(29) for _ in cipher]
    for start,w in words:
        candidates=dictionary.get(len(w),[])
        if candidates:
            selected=candidates[rng.randrange(len(candidates))][1]
            plain[start:start+len(w)]=selected
    key=[rng.randrange(29) for _ in range(period)]
    if mode=='SUB': synthetic=[(p+key[i%period])%29 for i,p in enumerate(plain)]
    elif mode=='ADD': synthetic=[(p-key[i%period])%29 for i,p in enumerate(plain)]
    else: synthetic=[(key[i%period]-p)%29 for i,p in enumerate(plain)]
    newwords=[(s,synthetic[s:s+len(w)]) for s,w in words]
    return synthetic,newwords,sha(bytes(key))
def run(repo):
    plan=json.loads((P/'plan.json').read_text(encoding='utf-8'))
    src,source_sha=load_source(repo,plan)
    src['load_lp_words']()
    dictionary=src['LP_WORDS_BY_LEN']; wordset=src['LP_WORDS_SET']
    dict_rows=[{'length':L,'entries':[[name,list(gp)] for name,gp in items]} for L,items in sorted(dictionary.items())]
    dictionary_sha=sha((json.dumps(dict_rows,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8'))
    inputs=[]; targets=[]; source_runs=[]; observed=[]; plants=[]
    with tempfile.TemporaryDirectory() as tmp:
        base=Path(tmp); (base/'Tools').mkdir(); (base/'pages').mkdir()
        src['__file__']=str(base/'Tools'/'period_crib_solve.py')
        for target in plan['source_targets']:
            raw,site=source_page(repo,plan,target)
            dest=base/target['source_file']; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(raw)
            flat,words=src['parse_words'](dest)
            assert len(flat)==json.loads(site.read_text(encoding='utf-8'))['rune_count']
            inputs.append({'source_file':target['source_file'],'source_sha256':sha(raw),'site_file':str(site.relative_to(ROOT)).replace('\\','/'),'site_sha256':sha(site.read_bytes()),'current_page':target['current_page'],'period':target['period'],'runes':len(flat),'words':len(words)})
            targets.append((target,flat,words))
            out=io.StringIO()
            # The original command starts a fresh process for each page. Its function
            # appends dictionary entries on every call, so reuse would double votes.
            source_ns,_=load_source(repo,plan)
            source_ns['__file__']=str(base/'Tools'/'period_crib_solve.py')
            with contextlib.redirect_stdout(out): source_ns['solve_with_period'](int(target['source_file'].split('page_')[1][:2]),target['period'],verbose=False)
            source_runs.append({'page':target['current_page'],'period':target['period'],'stdout_sha256':sha(out.getvalue().encode('utf-8')),'text':out.getvalue()})
            for mode in plan['modes']:
                key,conf,tries=voted_key(flat,words,target['period'],mode,dictionary)
                plain=apply(flat,key,mode)
                observed.append({'page':target['current_page'],'period':target['period'],'mode':mode,'source_vote_cribs':tries,'unrefined_key_sha256':sha(bytes(key)),'unrefined_decode_sha256':sha(bytes(plain)),'source_unbounded_substring_score':src['lp_score'](plain),
                                 'folds':[heldout(flat,words,target['period'],mode,dictionary,wordset,fold) for fold in (0,1)]})
                planted,pwords,secret_sha=plant(flat,words,target['period'],mode,dictionary,33014317+target['period']*3+plan['modes'].index(mode))
                p=[heldout(planted,pwords,target['period'],mode,dictionary,wordset,fold) for fold in (0,1)]
                plants.append({'page':target['current_page'],'mode':mode,'period':target['period'],'secret_key_sha256':secret_sha,'folds':p})
    # Control preserves source word boundaries and original rune inventory separately per page.
    rng=random.Random(33014317); null=[]
    for t in range(199):
        peaks=[]
        for target,flat,words in targets:
            shuffled=flat[:];rng.shuffle(shuffled)
            sw=[(start,shuffled[start:start+len(w)]) for start,w in words]
            for mode in plan['modes']:
                for fold in (0,1):
                    h=heldout(shuffled,sw,target['period'],mode,dictionary,wordset,fold)
                    peaks.append({'page':target['current_page'],'mode':mode,'fold':fold,'hits':h['hits'],'eligible':h['eligible'],'rate':h['rate']})
        null.append({'trial':t,'best':max(peaks,key=lambda h:(h['rate'],h['hits']))})
    observed_folds=[{'page':o['page'],'mode':o['mode'],'fold':i,**f} for o in observed for i,f in enumerate(o['folds'])]
    best=max(observed_folds,key=lambda h:(h['rate'],h['hits']))
    positive_min=min(f['rate'] for x in plants for f in x['folds'])
    summary={'schema':'liberpedia-wulfic-periodic-crib-v1','plan_sha256':sha((P/'plan.json').read_bytes()),'source_sha256':source_sha,'dictionary_sha256':dictionary_sha,'dictionary_entries':sum(len(x['entries']) for x in dict_rows),'dictionary_unique':len(wordset),'inputs':inputs,'source_runs':[{'page':r['page'],'period':r['period'],'stdout_sha256':r['stdout_sha256']} for r in source_runs],'observed_folds':observed_folds,'selected_best':best,'positive_min_rate':positive_min,'positive_gate_passed':positive_min>=.5,'null_selected_rates':[x['best']['rate'] for x in null], 'null_ge_observed':sum(x['best']['rate']>=best['rate'] for x in null),'interpretation_gate':'Use selected null rank only if all six planted matching-direction, both-fold controls reach 50% held-out exact dictionary words.'}
    return {'summary':summary,'dictionary':dict_rows,'source_runs':source_runs,'observed':observed,'plants':plants,'null':null}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source-root',required=True,type=Path); ap.add_argument('--check',action='store_true'); x=ap.parse_args()
    outputs=run(x.source_root)
    for name,value in outputs.items():
        path=P/f'{name}.json'; content=json.dumps(value,ensure_ascii=False,indent=2)+'\n'
        if x.check: assert path.read_text(encoding='utf-8')==content,name
        else: path.write_text(content,encoding='utf-8',newline='\n')
    print({k:v for k,v in outputs['summary'].items() if k in ('dictionary_entries','dictionary_unique','selected_best','positive_min_rate','positive_gate_passed','null_ge_observed')})
if __name__=='__main__':main()
