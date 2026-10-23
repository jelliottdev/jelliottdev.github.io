"""Independent complete-grid check, including all 199 selected-max controls."""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MAP={chr(cp):i for i,cp in enumerate([
    0x16A0,0x16A2,0x16A6,0x16A9,0x16B1,0x16B3,0x16B7,0x16B9,0x16BB,
    0x16BE,0x16C1,0x16C4,0x16C7,0x16C8,0x16C9,0x16CB,0x16CF,0x16D2,
    0x16D6,0x16D7,0x16DA,0x16DD,0x16DF,0x16DE,0x16AA,0x16AB,0x16A3,
    0x16E1,0x16E0])}
SEP=set('-. \n\r\t\u2022•/&$%')


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def plain(c,k,mode):
    return ((c-k) if mode=='sub' else (c+k) if mode=='add' else (k-c))%29


def parse(text):
    seq=[]; lengths=[]; current=0
    for ch in text:
        if ch in MAP:
            seq.append(MAP[ch]); current+=1
        elif ch in SEP and current:
            lengths.append(current); current=0
    if current: lengths.append(current)
    positions=[]; pos=0
    for length in lengths:
        if length==1: positions.append(pos)
        pos+=length
    return seq,lengths,positions


def keys(number):
    limit=1_000_000
    sieve=[True]*(limit+1)
    sieve[0]=sieve[1]=False
    for p in range(2,1001):
        if sieve[p]:
            for multiple in range(p*p,limit+1,p): sieve[multiple]=False
    primes=[i for i,isprime in enumerate(sieve) if isprime]
    nested=[]
    for i in range(min(50_000,len(primes))):
        index=primes[i]-1
        if index<len(primes): nested.append(primes[index])
    x=int(number); base=[]
    while x: base.insert(0,x%29); x//=29
    return {'pip':[p%29 for p in nested],
            'ps-digits':[int(c) for c in number],
            'ps-pairs':[int(number[i:i+2])%29 for i in range(0,len(number)-1,2)],
            'ps-base29':base},nested


def examine(pages,keyset,flats,details=False):
    total=0; hits=0; best=None; perpage=[]; branch={}
    for page,seq in zip(pages,flats):
        n=len(seq); local_count=0; local_hits=0; local_best=None
        for name,key in keyset.items():
            ceiling=min(1000 if name=='pip' else 50,len(key)-n)
            for offset in range(max(0,ceiling)):
                for mode in ('sub','add','beaufort'):
                    if any(plain(seq[i],key[offset+i],mode) not in (10,24) for i in page['singletons']):
                        continue
                    counts=Counter(plain(c,key[offset+i],mode) for i,c in enumerate(seq))
                    score=29*sum(v*(v-1) for v in counts.values())/(n*(n-1))
                    candidate=(score,page['id'],name,offset,mode)
                    total+=1;local_count+=1
                    if score>1.3: hits+=1;local_hits+=1
                    if best is None or candidate>best: best=candidate
                    if local_best is None or candidate>local_best: local_best=candidate
                    if name not in branch or candidate>branch[name]: branch[name]=candidate
        if details:
            perpage.append((page['id'],local_count,local_hits,local_best))
    return total,hits,best,perpage,branch


def candidate(c):
    if c is None: return None
    score,page,name,offset,mode=c
    return {'normalized_ioc':round(score,9),'page':page,'key':name,'offset':offset,'mode':mode}


def main():
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    gate=json.loads((HERE/'gate.json').read_text(encoding='utf-8'))
    saved=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    audits=json.loads((HERE/'input-audit.json').read_text(encoding='utf-8'))
    assert sha(HERE/'plan.json')==gate['plan_sha256']==saved['plan_sha256']
    assert sha(HERE/'input-audit.json')==plan['input_manifest']['sha256']
    keyset,pips=keys(plan['source_rules']['ps_number'])
    assert {k:len(v) for k,v in keyset.items()}==gate['key_lengths']
    assert pips[:20]==gate['pip_first20']
    pages=[]
    for audit in audits:
        path=ROOT/'data/pages'/f"{audit['page']}.json"
        assert sha(path)==audit['site_sha256']
        page=json.loads(path.read_text(encoding='utf-8'))
        seq,lengths,singles=parse(page['raw'])
        assert len(seq)==audit['length'] and lengths==audit['source_word_lengths']
        pages.append({'id':audit['page'],'old':audit['old'],'flat':seq,'singletons':singles})
    assert len(pages)==34
    assert all(p['old']==21+i for i,p in enumerate(pages))
    grid={k:0 for k in keyset}
    for page in pages:
        n=len(page['flat'])
        for name,key in keyset.items():
            grid[name]+=3*max(0,min(1000 if name=='pip' else 50,len(key)-n))
    assert grid==gate['configuration_counts'] and sum(grid.values())==102036
    known=json.loads((ROOT/'data/pages/lp1-10.json').read_text(encoding='utf-8'))
    known_indices=[MAP[ch] for ch in known['reviewed_text'] if ch in MAP]
    expected_controls=[]
    for name,key in keyset.items():
        count=100 if len(key)>=105 else 60
        message=known_indices[:count]+[10,24]
        for mode in ('sub','add','beaufort'):
            ciphertext=[((p+k) if mode=='sub' else (p-k) if mode=='add' else (k-p))%29
                        for p,k in zip(message,key[3:3+len(message)])]
            recovered=[plain(c,key[3+i],mode) for i,c in enumerate(ciphertext)]
            assert recovered==message and recovered[-2:]==[10,24]
            freq=Counter(recovered); n=len(recovered)
            score=29*sum(v*(v-1) for v in freq.values())/(n*(n-1))
            assert score>1.3
            expected_controls.append({'key':name,'mode':mode,'offset':3,'length':n,
                                      'exact_recovery':True,'singleton_pass':True,
                                      'normalized_ioc':round(score,9)})
    assert expected_controls==gate['positive_controls']
    observed=examine(pages,keyset,[p['flat'] for p in pages],True)
    total,hits,best,perpage,branch=observed
    assert (total,hits)==(saved['observed']['admissible'],saved['observed']['above_1_3'])
    assert candidate(best)==saved['observed']['global_best']
    assert {k:candidate(v) for k,v in branch.items()}==saved['observed']['branch_max']
    for row,actual in zip(saved['observed']['page_details'],perpage):
        pid,cnt,n_hit,top=actual
        assert (row['page'],row['admissible'],row['above_1_3'],row['best'])==(pid,cnt,n_hit,candidate(top))
    rng=random.Random(20261023)
    greater=0
    assert len(saved['controls'])==199
    for trial,receipt in enumerate(saved['controls'],1):
        flats=[]
        for page in pages:
            sample=page['flat'][:];rng.shuffle(sample);flats.append(sample)
        admissible,n_hits,maximum,_,_=examine(pages,keyset,flats)
        rounded=None if maximum is None else round(maximum[0],9)
        assert receipt=={'trial':trial,'max_normalized_ioc':rounded,
                         'admissible':admissible,'above_1_3':n_hits}
        if rounded is not None and rounded>=saved['observed']['global_best']['normalized_ioc']:
            greater+=1
    assert greater==saved['controls_at_least_observed']
    assert 29*1.0<1.3*29 and 1.0<1.3 # Source raw gate is unreachable.
    print(f'Independent full-grid and 199 null sweeps passed; observed {total} admissible settings, {hits} over 1.3; {greater}/199 null maxima >= observed.')


if __name__=='__main__': main()
