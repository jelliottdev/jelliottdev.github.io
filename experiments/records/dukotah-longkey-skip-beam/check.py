"""Independent source-rule beam and 54-case/36-plant reconstruction."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUNES='ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
LATIN=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S','T','B','E','M','L','NG','OE','D','A','AE','Y','IA','EA')
CHAR={s:i for i,s in enumerate(LATIN) if len(s)==1}
CHAR.update({'V':1,'K':5,'Z':15,'Q':5})


def corpus():
    source=(HERE/'source/data/krisyotam_runes.txt').read_text(encoding='utf-8')
    pages=[[RUNES.index(c) for c in part if c in RUNES]
           for part in source.split('%') if any(c in RUNES for c in part)]
    assert len(pages)==57
    for i,p in enumerate(pages):
        site=i if i<50 else i+1
        page=json.loads((ROOT/f'data/pages/lp2-{site:02}.json').read_text(encoding='utf-8'))
        assert p==[RUNES.index(c) for c in page['raw'] if c in RUNES]
    return pages


def key_stream(name):
    filename='pgp_english_prose' if name=='pgp_prose' else name
    text=(HERE/f'source/analysis/armada20/{filename}.txt').read_text(encoding='utf-8',errors='ignore')
    return [CHAR[c] for c in text.upper() if c in CHAR]


def score_model():
    counts={};total=0
    for row in (HERE/'source/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,n=row.split();n=int(n);counts[gram]=n;total+=n
    t=math.log10(total)
    return {q:math.log10(n)-t for q,n in counts.items()},math.log10(.01)-t


def total_score(text,weights,floor):
    if len(text)<4:return -999.0
    return sum(weights.get(text[i:i+4],floor) for i in range(len(text)-3))


def norm_score(text,weights,floor):
    return total_score(text,weights,floor)/(len(text)-3)


def beam(cipher,key,offset,weights,floor,trace=False):
    states={offset:(0.0,())}
    for value in cipher:
        next_states={}
        for position,(partial,path) in states.items():
            for advance in (1,2):
                new_position=position+advance
                if new_position>=len(key):continue
                plain=(value-key[new_position])%29
                new_path=path+(plain,)
                tail=''.join(LATIN[x] for x in new_path[-4:])
                bump=total_score(tail,weights,floor) if len(new_path)>=4 else 0.0
                cumulative=partial+bump
                if new_position not in next_states or cumulative>next_states[new_position][0]:
                    next_states[new_position]=(cumulative,new_path)
        states=dict(sorted(next_states.items(),key=lambda item:-item[1][0])[:120])
        if not states:break
    if not states:return (-99.0,'',0,()) if trace else (-99.0,'',0)
    best=None
    for _,(_,path) in states.items():
        text=''.join(LATIN[x] for x in path)
        value=norm_score(text,weights,floor)
        if best is None or value>best[0]:best=(value,text,len(path),path)
    return best if trace else best[:3]


def plant(message,key,offset,collision):
    cipher=[];position=offset;skips=0
    for value in message:
        proposed=(value+key[position+1])%29
        if collision and cipher and proposed==cipher[-1]:position+=2;skips+=1
        else:position+=1
        cipher.append((value+key[position])%29)
    return cipher,skips


if __name__=='__main__':
    data=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert data['plan_sha256']==hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()
    pages=corpus();weights,floor=score_model();sample=sorted(range(55),key=lambda i:-len(pages[i]))[:6]
    assert sample==[29,43,47,11,17,21]
    with (ROOT/'exports/readings/lp2-56.csv').open(encoding='utf-8',newline='') as f:
        known=[int(row['output_index']) for row in csv.DictReader(f)]
    assert len(known)==85
    keys={name:key_stream(name) for name in ('taoteching','thomas','pgp_prose')}
    assert [len(keys[x]) for x in keys]==[3596,23369,2782]
    actual=[]
    for name,key in keys.items():
        for page_index in sample:
            for offset in (0,len(key)//4,len(key)//2):
                value,text,n=beam(pages[page_index],key,offset,weights,floor)
                actual.append((name,page_index,offset,value,text,n))
    assert len(actual)==len(data['real'])==54
    for output,rec in zip(actual,data['real']):
        name,page_index,offset,value,text,n=output
        assert (name,page_index,offset)==(rec['key_text'],rec['source_page'],rec['offset'])
        assert n==rec['cipher_runes']==len(pages[page_index])
        assert abs(value-rec['score'])<1e-10
        assert len(text)==rec['latin_length'] and text[:80]==rec['preview']
        assert hashlib.sha256(text.encode('ascii')).hexdigest()==rec['plaintext_sha256']
    print('PASS all 54 source-rule manuscript outputs, complete paths and page mapping',flush=True)
    messages={'documented-85':known,'repeated-273':(known*4)[:273]}
    for rec in data['controls']:
        key=keys[rec['key_text']];message=messages[rec['message']]
        cipher,skips=plant(message,key,rec['offset'],rec['mechanism']=='collision-skip')
        value,text,n=beam(cipher,key,rec['offset'],weights,floor)
        truth=''.join(LATIN[x] for x in message)
        assert skips==rec['planted_skips'] and n==len(cipher)==rec['cipher_runes']
        assert (text==truth)==rec['plaintext_exact']
        assert (value>-5)==rec['above_source_bar']
        assert abs(value-rec['source_score'])<1e-10
        assert hashlib.sha256(text.encode('ascii')).hexdigest()==rec['output_sha256']
    assert len(data['controls'])==36
    assert data['control_counts']=={
        'no_skip_exact':sum(r['plaintext_exact'] for r in data['controls'] if r['mechanism']=='no-skip'),
        'collision_skip_exact':sum(r['plaintext_exact'] for r in data['controls'] if r['mechanism']=='collision-skip'),
        'collision_skip_above_bar':sum(r['above_source_bar'] for r in data['controls'] if r['mechanism']=='collision-skip')}
    assert data['real_above_source_bar']==sum(r['score']>-5 for r in data['real'])==0
    print('PASS all 36 plants and source threshold checks')
