"""Independent dictionary, source-key and held-out control checks."""
import argparse, ast, hashlib, json, re, subprocess
from collections import defaultdict
from pathlib import Path
P=Path(__file__).resolve().parent; ROOT=P.parents[2]
RUNE_ORDER=[0x16A0,0x16A2,0x16A6,0x16A9,0x16B1,0x16B3,0x16B7,0x16B9,0x16BB,0x16BE,0x16C1,0x16C4,0x16C7,0x16C8,0x16C9,0x16CB,0x16CF,0x16D2,0x16D6,0x16D7,0x16DA,0x16DD,0x16DF,0x16DE,0x16AA,0x16AB,0x16A3,0x16E1,0x16E0]
IDX={x:i for i,x in enumerate(RUNE_ORDER)}
LETTER={'F':0,'U':1,'V':1,'O':3,'R':4,'C':5,'K':5,'G':6,'W':7,'H':8,'N':9,'I':10,'J':11,'P':13,'X':14,'S':15,'T':16,'B':17,'E':18,'M':19,'L':20,'D':23,'A':24,'Y':26}
DIGRAPH={'TH':2,'EO':12,'NG':21,'OE':22,'AE':25,'IA':27,'EA':28}
def hashbytes(b):return hashlib.sha256(b).hexdigest()
def encode(word):
    word=word.upper(); out=[]; i=0
    while i<len(word):
        if word[i:i+2] in DIGRAPH: out.append(DIGRAPH[word[i:i+2]]); i+=2
        elif word[i] in LETTER: out.append(LETTER[word[i]]); i+=1
        else:i+=1
    return out
def parse(raw):
    flat=[]; words=[]; cur=[]; start=0
    for line in raw.splitlines():
        line=line.rstrip(); a=sum(c.isascii() and c.isalpha() for c in line); r=sum(ord(c) in IDX for c in line)
        if a>0 and r==0 or a>2 and r<a:continue
        for c in line:
            if ord(c) in IDX:cur.append(IDX[ord(c)])
            elif c in '-./&$\n' and cur:
                words.append((start,cur)); flat+=cur; cur=[];start=len(flat)
    if cur:words.append((start,cur));flat+=cur
    return flat,words
def vote(cipher,words,period,mode,dictionary):
    baskets=[{} for _ in range(period)]
    accepted=0
    for start,word in words:
        if not 2<=len(word)<=15:continue
        for _,plain in dictionary[len(word)]:
            inferred={}
            for j in range(len(word)):
                residue=(start+j)%period; c=word[j];p=plain[j]
                k=(c-p)%29 if mode=='SUB' else (p-c)%29 if mode=='ADD' else (p+c)%29
                if residue in inferred and inferred[residue]!=k:break
                inferred[residue]=k
            else:
                accepted+=1
                for residue,k in inferred.items():
                    baskets[residue][k]=baskets[residue].get(k,0)+1
    keys=[max(b,key=b.get) if b else 0 for b in baskets]
    return keys,accepted
def decode(cipher,key,mode):
    if mode=='SUB':return [(c-key[i%len(key)])%29 for i,c in enumerate(cipher)]
    if mode=='ADD':return [(c+key[i%len(key)])%29 for i,c in enumerate(cipher)]
    return [(key[i%len(key)]-c)%29 for i,c in enumerate(cipher)]
def fold(cipher,words,period,mode,dictionary,valid,parity):
    training=[w for i,w in enumerate(words) if i%2==parity]
    key,accepted=vote(cipher,training,period,mode,dictionary)
    plain=decode(cipher,key,mode)
    test=[(s,w) for i,(s,w) in enumerate(words) if i%2!=parity and 2<=len(w)<=15]
    hits=sum(tuple(plain[s:s+len(w)]) in valid for s,w in test)
    return hits,len(test),hashbytes(bytes(key)),accepted
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',required=True,type=Path);a=ap.parse_args()
    plan=json.loads((P/'plan.json').read_text(encoding='utf-8'))
    results=json.loads((P/'summary.json').read_text(encoding='utf-8'))
    inputs=json.loads((P/'dictionary.json').read_text(encoding='utf-8'))
    observed=json.loads((P/'observed.json').read_text(encoding='utf-8'))
    plants=json.loads((P/'plants.json').read_text(encoding='utf-8'))
    null=json.loads((P/'null.json').read_text(encoding='utf-8'))
    runs=json.loads((P/'source_runs.json').read_text(encoding='utf-8'))
    raw=subprocess.check_output(['git','show',f"{plan['source_revision']}:{plan['primary_source']['path']}"],cwd=a.source_root)
    assert hashbytes(raw)==results['source_sha256']
    blob=subprocess.check_output(['git','rev-parse',f"{plan['source_revision']}:{plan['primary_source']['path']}"],cwd=a.source_root,text=True).strip()
    assert blob==plan['primary_source']['git_blob']
    tree=ast.parse(raw.decode('utf-8'))
    func=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='load_lp_words')
    words=next(ast.literal_eval(x.value) for x in ast.walk(func) if isinstance(x,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='lp_vocab_latin' for t in x.targets))
    dictionary=defaultdict(list)
    for w in words:
        gp=encode(w)
        if gp:dictionary[len(gp)].append((w,gp))
    expected=[{'length':n,'entries':[[w,g] for w,g in entries]} for n,entries in sorted(dictionary.items())]
    assert expected==inputs
    packed=(json.dumps(expected,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode('utf-8')
    assert results['dictionary_sha256']==hashbytes(packed)
    valid={tuple(g) for entries in dictionary.values() for _,g in entries}
    assert results['dictionary_entries']==len(words)==335 and results['dictionary_unique']==len(valid)==309
    for item in results['inputs']:
        p=ROOT/item['site_file'];assert hashbytes(p.read_bytes())==item['site_sha256']
        src=subprocess.check_output(['git','show',f"{plan['source_revision']}:{item['source_file']}"],cwd=a.source_root)
        assert hashbytes(src)==item['source_sha256']
        site=json.loads(p.read_text(encoding='utf-8'))['raw'].encode('utf-8')
        assert src.strip()==site.strip()
        cipher,slots=parse(src.decode('utf-8'))
        assert len(cipher)==item['runes'] and len(slots)==item['words']
        for mode in plan['modes']:
            row=next(x for x in observed if x['page']==item['current_page'] and x['mode']==mode)
            key,accepted=vote(cipher,slots,item['period'],mode,dictionary)
            assert hashbytes(bytes(key))==row['unrefined_key_sha256']
            assert hashbytes(bytes(decode(cipher,key,mode)))==row['unrefined_decode_sha256']
            assert accepted==row['source_vote_cribs']
            for k in (0,1):
                hits,total,ks,tries=fold(cipher,slots,item['period'],mode,dictionary,valid,k)
                saved=row['folds'][k]
                assert (hits,total,ks,tries)==(saved['hits'],saved['eligible'],saved['key_sha256'],saved['vote_cribs'])
    # Published null ranks are arithmetic receipts, not interpreted after the positive gate fails.
    assert len(null)==199 and [x['best']['rate'] for x in null]==results['null_selected_rates']
    assert results['positive_min_rate']==min(f['rate'] for row in plants for f in row['folds'])==0
    assert not results['positive_gate_passed']
    assert results['null_ge_observed']==199
    assert len(runs)==2 and all(hashbytes(r['text'].encode('utf-8'))==r['stdout_sha256'] for r in runs)
    for row,run in zip(results['source_runs'],runs):
        assert row['stdout_sha256']==run['stdout_sha256']
        keys=[json.loads(k) for k in re.findall(r'Derived key: (\[[^\]]+\])',run['text'])]
        assert len(keys)==3
        for mode,key in zip(plan['modes'],keys):
            observed_row=next(x for x in observed if x['page']==run['page'] and x['mode']==mode)
            assert hashbytes(bytes(key))==observed_row['unrefined_key_sha256']
    print('PASS: pinned source dictionary and page bytes, six original vote keys, 12 independent held-out folds, source stdout keys, control-gate arithmetic')
if __name__=='__main__':main()
