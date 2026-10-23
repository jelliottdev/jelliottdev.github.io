"""Independent 45-route, 10-page and 199-null checker for the source replay."""
import argparse
import collections
import hashlib
import json
import pathlib
import random
import subprocess

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT.parent/'source-archives'/'Wulfic-Cicada3301-Liber_Primus'
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LATIN=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
PRIMES=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109)
MAP={c:i for i,c in enumerate(RUNES)}
CONFIG={21:([5,24,17,24,20],'beaufort'),22:([23,10,1,10,9,10,16,26],'beaufort'),
        23:([18,9,5,4,26,13,16,10,3,9],'add'),24:([3,17,15,5,1,4,24],'beaufort'),
        25:([5,24,17,24,20],'beaufort'),26:([18,9,5,4,26,13,16],'add'),
        27:([15,8,24,23,3,7,15],'add'),28:([23,18,3,4],'sub'),
        29:([16,3,16,10,18,9,16],'beaufort'),30:([19,3,1,4,9,0,1,20],'add')}
def sha(b):return hashlib.sha256(b).hexdigest()
def primes_upto(n):
    a=[True]*(n+1);a[:2]=[False,False]
    for x in range(2,int(n**0.5)+1):
        if a[x]:
            for y in range(x*x,n+1,x):a[y]=False
    return {x for x,v in enumerate(a) if v}
def fib_upto(n):
    a,b=1,2;out=set()
    while a<=n:out.add(a);a,b=b,a+b
    return out
def words(raw):
    out=[];cur=[]
    for c in raw:
        if c in MAP:cur.append(MAP[c])
        elif c in '-. \n\r&$%/' and cur:out.append(cur);cur=[]
    if cur:out.append(cur)
    return out
def decode(a,key,mode):
    if mode=='add':return [(c+key[i%len(key)])%29 for i,c in enumerate(a)]
    if mode=='sub':return [(c-key[i%len(key)])%29 for i,c in enumerate(a)]
    return [(key[i%len(key)]-c)%29 for i,c in enumerate(a)]
def ioc(a):
    n=len(a)
    if n<2:return 0
    hist=collections.Counter(a)
    return 29*sum(v*(v-1) for v in hist.values())/(n*(n-1))
def latin(a):return ''.join(LATIN[i] for i in a)
def score(parts,lex):
    value=0;matched=[]
    for word in parts:
        for candidate in (word,word.replace('IA','ION'),word.replace('C','K'),word.replace('U','V')):
            if candidate in lex:
                value+=len(candidate)**2;matched.append(candidate);break
    return value,matched
def route_rows(raw,lex,old):
    cipher=[MAP[c] for c in raw if c in MAP]
    source_words=words(raw)
    key,mode=CONFIG[old]
    decoded=decode(cipher,key,mode)
    dwords=[];at=0
    for w in source_words:dwords.append(decoded[at:at+len(w)]);at+=len(w)
    assert at==len(decoded)
    n=len(decoded);ps=primes_upto(n+1)
    routes={}
    for offset,suffix in ((0,'0idx'),(1,'1idx')):
        selected=[i for i in range(n) if i+offset in ps]
        other=[i for i in range(n) if i+offset not in ps]
        routes['prime_pos_'+suffix]=[decoded[i] for i in selected]
        routes['nonprime_pos_'+suffix]=[decoded[i] for i in other]
        routes['prime_then_nonprime_'+suffix]=[decoded[i] for i in selected+other]
    routes['reverse']=decoded[::-1]
    for width in (5,7,11,13,17,19,23,29,31):
        order=[row*width+col for col in range(width) for row in range((n+width-1)//width) if row*width+col<n]
        routes[f'grid_cols_w{width}']=[decoded[i] for i in order]
        rows=(n+width-1)//width;cells={};pos=0
        for col in range(width):
            for row in range(rows):
                if pos<n:cells[(row,col)]=pos;pos+=1
        routes[f'grid_rows_w{width}']=[decoded[cells[row,col]] for row in range(rows) for col in range(width) if (row,col) in cells]
    for width in (5,7,11,13):
        rows=(n+width-1)//width;long=n%width or width;cols=[];at=0
        for col in range(width):
            size=rows if col<long else rows-1
            cols.append(list(range(at,at+size)));at+=size
        routes[f'undo_col_w{width}']=[decoded[cols[col][row]] for row in range(rows) for col in range(width) if row<len(cols[col])]
    for skip in (2,3,5,7,11,13):
        routes[f'skip_{skip}']=[decoded[i] for residue in range(skip) for i in range(residue,n,skip)]
    fs=fib_upto(n)
    routes['fibonacci_pos']=[decoded[i] for i in range(n) if i+1 in fs]
    routes['sort_by_gp_value']=sorted(decoded,key=lambda x:PRIMES[x])
    routes['read_at_primes']=[decoded[i] for i in range(n) if i+1 in ps]
    pw=primes_upto(len(dwords)+1)
    word_routes={
      'words_reverse':dwords[::-1],
      'words_prime_first':[dwords[i] for i in range(len(dwords)) if i+1 in pw]+[dwords[i] for i in range(len(dwords)) if i+1 not in pw],
      'words_by_length':sorted(dwords,key=len),
      'words_by_gp_sum':sorted(dwords,key=lambda w:sum(PRIMES[i] for i in w)),
      'words_by_first_char':sorted(dwords,key=lambda w:PRIMES[w[0]] if w else 0),
      'words_internal_sort_gp':[sorted(w,key=lambda x:PRIMES[x]) for w in dwords],
      'words_internal_reverse':[w[::-1] for w in dwords]}
    out={}
    for label,arr in routes.items():
        text=latin(arr);v,found=score([text],lex)
        out[label]={'label':label,'word_score':v,'ioc':ioc(arr),'preview':text[:150],'word_matches':found[:10]}
    for label,group in word_routes.items():
        parts=[latin(w) for w in group];flat=[v for w in group for v in w];v,found=score(parts,lex)
        out[label]={'label':label,'word_score':v,'ioc':ioc(flat),'preview':' '.join(parts)[:150],'word_matches':found[:10]}
    assert len(out)==45,len(out)
    baseline=score([latin(w) for w in dwords],lex)[0]
    return out,ioc(decoded),baseline,len(source_words)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source-root',type=pathlib.Path,default=SOURCE);args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf8'))
    saved=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    assert saved['plan_sha256']==sha((HERE/'plan.json').read_bytes())
    assert subprocess.check_output(['git','-C',str(args.source_root),'rev-parse','HEAD']).decode().strip()==plan['source_revision']
    def blob(rel):
        b=subprocess.check_output(['git','-C',str(args.source_root),'show',plan['source_revision']+':'+rel])
        assert sha(b)==plan['source_files'][rel]['sha256']
        return b
    lex={w.strip().upper() for w in blob('data/corpora/wordlist.txt').decode().splitlines() if len(w.strip())>=2}
    assert len(lex)==saved['source_wordlist_size']
    originals=[]
    subset={'prime_pos_0idx','prime_pos_1idx','nonprime_pos_0idx','nonprime_pos_1idx','fibonacci_pos','read_at_primes'}
    word_order={'words_reverse','words_prime_first','words_by_length','words_by_gp_sum','words_by_first_char'}
    inv=collections.Counter()
    for old,saved_page in zip(range(21,31),saved['pages']):
        raw=blob(f'pages/page_{old:02d}/runes.txt').decode('utf8').strip();originals.append((old,raw))
        site=ROOT/f'data/pages/lp2-{old-17:02d}.json'
        assert sha(site.read_bytes())==plan['site_pages'][f'lp2-{old-17:02d}']
        assert [MAP[c] for c in raw if c in MAP]==[MAP[c] for c in json.loads(site.read_text(encoding='utf8'))['raw'] if c in MAP]
        rows,baseline_ioc,baseline_score,nwords=route_rows(raw,lex,old)
        assert saved_page['page']==f'lp2-{old-17:02d}' and saved_page['runes']==sum(c in MAP for c in raw) and saved_page['words']==nwords
        assert abs(saved_page['baseline_ioc']-baseline_ioc)<1e-12 and saved_page['baseline_score']==baseline_score
        assert {r['label']:r for r in saved_page['rows']}==rows
        for label,row in rows.items():
            if label in subset:inv['subset_cases']+=1
            else:assert abs(row['ioc']-baseline_ioc)<1e-12;inv['full_length_ioc_cases']+=1
            if label in word_order:assert row['word_score']==baseline_score;inv['word_order_score_cases']+=1
    assert dict(inv)==saved['invariants']
    control=saved['control'];known=[]
    single={v:i for i,v in enumerate(LATIN) if len(v)==1}
    for w in control['selected_words']:known.extend(single[c] for c in w)
    assert sha(bytes(known))==control['known_sha256']
    assert score(control['selected_words'],lex)[0]==control['known_spaced_score']>0
    assert score([latin(known)],lex)[0]==control['known_flat_score']==0
    key,mode=CONFIG[21];pre=known[::-1]
    if mode=='beaufort':cipher=[(key[i%len(key)]-v)%29 for i,v in enumerate(pre)]
    elif mode=='add':cipher=[(v-key[i%len(key)])%29 for i,v in enumerate(pre)]
    else:cipher=[(v+key[i%len(key)])%29 for i,v in enumerate(pre)]
    assert sha(bytes(cipher))==control['cipher_sha256']
    assert decode(cipher,key,mode)[::-1]==known and control['full_route_recovery']
    it=iter(cipher);raw=''.join(RUNES[next(it)] if c in MAP else c for c in originals[0][1])
    planted,_,_,_=route_rows(raw,lex,21)
    assert planted['reverse']['word_score']==control['source_reverse_route_score']==0
    assert abs(planted['reverse']['ioc']-control['source_reverse_route_ioc'])<1e-12
    rng=random.Random(20261023)
    assert len(saved['null'])==199
    for trial,receipt in enumerate(saved['null']):
        peaks=[]
        for old,raw in originals:
            chars=[c for c in raw if c in MAP];rng.shuffle(chars);it=iter(chars)
            shuf=''.join(next(it) if c in MAP else c for c in raw)
            rows,_,_,_=route_rows(shuf,lex,old)
            peaks.append(max(r['word_score'] for r in rows.values()))
        assert receipt=={'trial':trial,'global_max_score':max(peaks),'page_max_scores':peaks}
    log=(HERE/'source-log.txt').read_text(encoding='utf8')
    assert 'Loaded 370079 English words' in log and log.count('Top 15 rearrangements (by English word score)')==10
    assert 'Score=  111' in log
    print('PASS: all 450 source route rows, 390 frequency invariants, 50 word-score invariants, positive route control and 199 full-grid shuffles')

if __name__=='__main__':main()
