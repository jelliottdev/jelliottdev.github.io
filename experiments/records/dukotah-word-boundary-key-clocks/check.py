"""Independent scalar reconstruction of boundary/word-clock winners and nulls."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from functools import lru_cache
from pathlib import Path

HERE=Path(__file__).resolve().parent
RUNES="ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ"
LATIN=("F","U","TH","O","R","C","G","W","H","N","I","J","EO","P","X","S","T","B","E","M","L","NG","OE","D","A","AE","Y","IA","EA")
PRIMES=(2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109)
GP={c:i for i,c in enumerate(RUNES)}
KEY=(23,10,1,10,9,10,16,26)


def source_pages():
    s=(HERE/'source/data/krisyotam_runes.txt').read_text(encoding='utf8')
    return [part for part in s.split('%') if any(ch in GP for ch in part)]


def scorer():
    counts={};total=0
    for line in (HERE/'source/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        w,n=line.split();n=int(n);counts[w]=n;total+=n
    t=math.log10(total)
    return {w:math.log10(n)-t for w,n in counts.items()},math.log10(.01)-t


def score(seq,model,floor):
    text=''.join(LATIN[v] for v in seq)
    return sum(model.get(text[i:i+4],floor) for i in range(len(text)-3))/(len(text)-3)


@lru_cache(None)
def prime_stream(n):
    out=[];v=2
    while len(out)<n:
        if all(v%p for p in out if p*p<=v):out.append(v)
        v+=1
    return out


def phi(n):
    result=n;factor=2
    while factor*factor<=n:
        if n%factor==0:
            while n%factor==0:n//=factor
            result-=result//factor
        factor+=1
    if n>1:result-=result//n
    return result


@lru_cache(None)
def stream(name,n):
    if name=='DIVINITY':return tuple(KEY[i%len(KEY)] for i in range(n))
    if name=='prime':return tuple(p%29 for p in prime_stream(n))
    if name=='prime_minus_1':return tuple((p-1)%29 for p in prime_stream(n))
    if name=='totient':return tuple(phi(i+2)%29 for i in range(n))
    raise ValueError(name)


def fh1(pages,model,floor):
    best=(-999,None);count=0
    for label,seps in [('-',set('-')),('-.',set('-.')),('-./',set('-./'))]:
        for key in ('prime','prime_minus_1','totient','DIVINITY'):
            for pi,raw in enumerate(pages):
                total=sum(ch in GP or ch in seps for ch in raw)
                schedule=stream(key,total+4);clock=0;plain=[]
                for ch in raw:
                    if ch in GP:
                        plain.append((GP[ch]-schedule[clock])%29);clock+=1
                    elif ch in seps:clock+=1
                value=score(plain,model,floor);count+=1
                if value>best[0]:best=(value,{'sepset':label,'key':key,'page':pi})
    return count,best


def fh3(pages,model,floor):
    best=(-999,None);count=0
    for label,resets in [('word',set('-')),('clause',set('.')),('line',set('/')),('segment',set('&$'))]:
        for key in ('DIVINITY','prime','prime_minus_1'):
            schedule=stream(key,300)
            for pi,raw in enumerate(pages):
                clock=0;plain=[]
                for ch in raw:
                    if ch in GP:
                        plain.append((GP[ch]-schedule[clock%300])%29);clock+=1
                    elif ch in resets:clock=0
                value=score(plain,model,floor);count+=1
                if value>best[0]:best=(value,{'reset':label,'key':key,'page':pi})
    return count,best


def words(raw):
    output=[];current=[]
    for ch in raw:
        if ch in GP:current.append(GP[ch])
        elif current:output.append(current);current=[]
    if current:output.append(current)
    return output


def wordsum(seq,variant,sign,atbash):
    if variant=='W5':
        output=[];previous=0
        for cipher in (c for word in seq for c in word):
            base=28-cipher if atbash else cipher
            output.append((base+sign*(PRIMES[previous]%29))%29)
            previous=cipher
        return output
    output=[];key=0;cumulative=0
    for word in seq:
        plain=[((28-c if atbash else c)+sign*key)%29 for c in word]
        output.extend(plain)
        cipher_sum=sum(PRIMES[c] for c in word)
        if variant=='W1':key=cipher_sum%29
        elif variant=='W2':key=sum(PRIMES[p] for p in plain)%29
        elif variant=='W3':cumulative+=cipher_sum;key=cumulative%29
        elif variant=='W4':key=phi(cipher_sum)%29
    return output


def wordgrid(pages,model,floor):
    best=(-999,None);by={};count=0
    for variant in ('W1','W2','W3','W4','W5'):
        local=(-999,None)
        for sign in (-1,1):
            for atbash in (False,True):
                for pi,raw in enumerate(pages):
                    p=wordsum(words(raw),variant,sign,atbash)
                    value=score(p,model,floor);count+=1
                    rec={'variant':variant,'sign':sign,'atbash':atbash,'source_page':pi,
                         'score':value,'plaintext_sha256':hashlib.sha256(bytes(p)).hexdigest()}
                    if value>local[0]:local=(value,rec)
                    if value>best[0]:best=(value,rec)
        by[variant]=local[1]
    return count,best,by


def shuffle(pages,rng):
    out=[]
    for raw in pages:
        chars=list(raw);positions=[i for i,ch in enumerate(chars) if ch in GP]
        symbols=[chars[i] for i in positions];rng.shuffle(symbols)
        for i,ch in zip(positions,symbols):chars[i]=ch
        out.append(''.join(chars))
    return out


def assert_best(actual,expected,keys):
    assert abs(actual[0]-expected['score'])<1e-10
    rec=expected.get('rec',expected)
    for key in keys:assert actual[1][key]==rec[key],(key,actual,expected)


if __name__=='__main__':
    saved=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    assert saved['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    pages=source_pages();assert len(pages)==57
    # The source omits the LP2-50 grid from its rune-only page stream.
    for source_index,raw in enumerate(pages):
        site_index=source_index if source_index<50 else source_index+1
        site=json.loads((HERE.parents[2]/f'data/pages/lp2-{site_index:02}.json').read_text(encoding='utf8'))
        assert ''.join(c for c in raw if c in GP)==''.join(c for c in site['raw'] if c in GP)
    model,floor=scorer();uns=pages[:55]
    count,a=fh1(uns,model,floor);assert count==660
    assert_best(a,saved['real']['FH1'],('sepset','key','page'))
    count,b=fh3(uns,model,floor);assert count==660
    assert_best(b,saved['real']['FH3'],('reset','key','page'))
    count,c,by=wordgrid(uns,model,floor);assert count==1100
    assert_best(c,saved['real']['word_sums']['best'],('variant','sign','atbash','source_page','plaintext_sha256'))
    for variant,rec in by.items():
        assert_best((rec['score'],rec),saved['real']['word_sums']['by_variant'][variant],('source_page','sign','atbash','plaintext_sha256'))
    expected=[int(r['output_index']) for r in csv.DictReader((HERE.parents[2]/'exports/readings/lp2-56.csv').open(encoding='utf8',newline=''))]
    source55=[ch for ch in pages[55]]
    clock=0;got=[];schedule=stream('prime_minus_1',300)
    for ch in source55:
        if ch in GP:got.append((GP[ch]-schedule[clock%300])%29);clock+=1
        elif ch in '&$':clock=0
    assert len(got)==len(expected)==85
    diagnostic=saved['known_page_diagnostic']
    assert sum(x==y for x,y in zip(got,expected))==diagnostic['matched_rune_positions']==56
    assert next(i for i,(x,y) in enumerate(zip(got,expected)) if x!=y)==diagnostic['first_mismatch_zero_based']==56
    assert diagnostic['total_rune_positions']==len(expected) and not diagnostic['full_reading_recovered']
    assert diagnostic['source_score']<diagnostic['source_threshold']
    print('PASS all real settings and 56/85 known-page check',flush=True)
    rng=random.Random(3301)
    counts={'FH1':0,'FH3':0,'word_sums':0}
    for i,ref in enumerate(saved['null_controls']):
        pp=shuffle(uns,rng)
        n1,x=fh1(pp,model,floor)
        n3,y=fh3(pp,model,floor)
        nw,z,_=wordgrid(pp,model,floor)
        assert (n1,n3,nw)==(660,660,1100)
        for key,value in [('FH1',x[0]),('FH3',y[0]),('word_sums',z[0])]:
            assert abs(value-ref[{'FH1':'FH1_best','FH3':'FH3_best','word_sums':'word_sums_best'}[key]])<1e-10
            observed={'FH1':a[0],'FH3':b[0],'word_sums':c[0]}[key]
            counts[key]+=value>=observed
        assert abs(max(x[0],y[0],z[0])-ref['global_best'])<1e-10
        print(f'PASS null {i+1}/49',flush=True)
    assert counts==saved['null_at_least_observed']
    print('PASS all complete-grid controls')
