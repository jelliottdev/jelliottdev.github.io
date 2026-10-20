"""Reproduce explicitly normalized later-message sums and the adjusted recurrence."""
from functools import lru_cache
import argparse
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'exports/later-message-sums.json'

def report():
    alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
    aliases={label:a['index'] for a in alphabet for label in a['aliases']}
    weights={a['index']:a['prime'] for a in alphabet}
    @lru_cache(None)
    def parse(word):
        if not word:return ((),)
        return tuple(sorted(set((index,)+rest for label,index in aliases.items() if word.startswith(label) for rest in parse(word[len(label):]))))
    def encode(text):
        words=[];stream=[]
        for match in re.finditer('[A-Za-z]+',text):
            normalized=match.group().upper().replace('V','U')
            choices=parse(normalized)
            if not choices:raise ValueError('Unencodable word: '+normalized)
            shortest=min(map(len,choices));best=[v for v in choices if len(v)==shortest]
            if len(best)!=1:raise ValueError('Ambiguous shortest encoding: '+normalized)
            selected=best[0];stream.extend(selected)
            words.append(dict(source=match.group(),span=[match.start(),match.end()],normalized=normalized,all_encodings=choices,selected=selected,prime_sum=sum(weights[i] for i in selected)))
        return dict(text=text,words=words,indices=stream,rune_count=len(stream),prime_sum=sum(weights[i] for i in stream))
    manifest=json.loads((ROOT/'data/evidence/later-messages.json').read_text())
    bodies={};inputs={}
    for record in manifest['records']:
        raw=(ROOT/record['payload_path']).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest!=record['payload_sha256']:raise ValueError('Message checksum mismatch')
        inputs[record['payload_path']]=digest
        text=raw.decode().replace('\r\n','\n')
        bodies[record['year']]=text.split('\n\n',1)[1].split('-----BEGIN PGP SIGNATURE-----',1)[0]
    inputs['data/index.json']=hashlib.sha256((ROOT/'data/index.json').read_bytes()).hexdigest()
    sentences=[s.strip() for s in bodies[2016].split('.') if s.strip()]
    if len(sentences)!=8:raise ValueError('Unexpected sentence partition')
    units=[encode('.'.join(sentences[:3])+'.'),encode(sentences[3]+'.'),encode('.'.join(sentences[4:])+'.')]
    latter=encode(bodies[2017]);full=encode(bodies[2016])
    # Independent longest-token walk agrees for these actual words; this is
    # a cross-check, not a claim that greedy parsing solves every token set.
    for word in full['words']+latter['words']:
        remaining=word['normalized'];greedy=[]
        while remaining:
            label=max((a for a in aliases if remaining.startswith(a)),key=len)
            greedy.append(aliases[label]);remaining=remaining[len(label):]
        assert greedy==list(word['selected'])
    assert [(u['rune_count'],u['prime_sum']) for u in units]==[(59,2999),(59,2819),(59,2581)]
    assert latter['prime_sum']==2131 and full['prime_sum']==8399
    assert units[-1]['indices'][-1]==0
    adjusted=[units[0]['prime_sum']+weights[0],units[1]['prime_sum'],units[2]['prime_sum']-weights[0]]
    primes=[]
    for candidate in range(2,4000):
        if all(candidate%p for p in primes if p*p<=candidate):primes.append(candidate)
    # Independent sieve checks the prime list used by the recurrence.
    sieve=[True]*4000;sieve[0]=sieve[1]=False
    for p in range(2,64):
        if sieve[p]:
            for multiple in range(p*p,4000,p):sieve[multiple]=False
    assert primes==[n for n in range(4000) if sieve[n]]
    fib=[0,1]
    while len(fib)<11:fib.append(sum(fib[-2:]))
    index=464;steps=[]
    for f in fib:
        index-=f;steps.append(dict(fibonacci=f,prime_index=index,prime=primes[index-1]))
    return dict(input_sha256=inputs,normalization='ASCII letter runs; uppercase; V to U; stored chart aliases; choose unique shortest encoding per run; ignore digits and punctuation, retain A and F from the key ID.',units_2016=units,body_2016=full,body_2017=latter,adjusted_sums=adjusted,adjusted_counts=[units[0]['rune_count']+1,units[1]['rune_count'],units[2]['rune_count']-1],recurrence=steps,conditional_match=[s['prime'] for s in steps[-4:]]==adjusted+[latter['prime_sum']],scope='Known-message arithmetic with an explicit terminal F relocation. Not an unedited recurrence, a prediction chronology claim or a new LP decryption.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=report()
    if args.check:
        assert json.loads(json.dumps(result))==json.loads(OUTPUT.read_text())
        print('PASS: complete word encodings, sums and adjusted recurrence reproduced')
    else:print(json.dumps(result,indent=2))
