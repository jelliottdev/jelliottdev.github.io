"""Independent source-receipt, planted-key and arithmetic checks."""
import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ARMS=('forward-chain-z28','backward-chain-z28','forward-chain-z29',
      'raw-z29','atbash-z29')


def ioc(xs,m):
    n=len(xs)
    return m*sum(v*(v-1) for v in Counter(xs).values())/(n*(n-1))


def primes(n):
    found=[]
    k=2
    while len(found)<n:
        if all(k%v for v in found if v*v<=k):
            found.append(k)
        k+=1
    return found


def receipt_rows(path):
    current=None
    j=0
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('===') and 'mod' in line and j<len(ARMS):
            current=ARMS[j];j+=1
        elif current is not None and ' top:' in line:
            section=re.search(r'(p\d+-\d+)\s+n=',line).group(1)
            values=re.findall(r'([0-9.]+) (\S+)@(\d+)([+-])',line)
            yield current,section,values


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-root',required=True)
    ap.add_argument('--text-root',required=True)
    args=ap.parse_args()
    source,text=Path(args.source_root),Path(args.text_root)
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    for name,want in plan['source_inputs'].items():
        assert hashlib.sha256((source/name).read_bytes()).hexdigest()==want,name
    for name,want in plan['text_sha256'].items():
        assert hashlib.sha256((text/'pages'/f'{name}.txt').read_bytes()).hexdigest()==want,name
    # Independently read every published top-three value rather than importing
    # the new replay engine. This checks 5 arms × 9 sections × 3 candidates.
    count=0
    for arm,section,source_top in receipt_rows(source/'results/tests4.txt'):
        ours=result['sections'][section]['source_arms'][arm]['top']
        assert len(source_top)==len(ours)==3
        for (v,name,offset,sign),recorded in zip(source_top,ours):
            assert (v,name,int(offset),sign)==(
                f"{recorded['ioc']:.3f}",recorded['sequence'],
                recorded['offset'],'+' if recorded['sign']==1 else '-')
            count+=1
    assert count==135
    # Reconstruct the planted plaintext with an independent prime generator.
    ds=json.loads((source/'dataset.json').read_text(encoding='utf-8'))
    plain=[v for s in ds['sections'] if s['solved'] for v in s['plain_indices']][:1200]
    assert len(plain)==1200
    prime=primes(1248)
    raw=[(p+prime[i+47])%29 for i,p in enumerate(plain)]
    recovered=[(raw[i]-prime[i+47])%29 for i in range(1200)]
    assert recovered==plain
    chain=[0]
    for i,p in enumerate(plain):
        chain.append((chain[-1]+1+(p%28+prime[i+47]%28)%28)%29)
    steps=[((chain[i]-chain[i-1])%29-1)%28 for i in range(1,len(chain))]
    recovered28=[(steps[i]-prime[i+47])%28 for i in range(1200)]
    assert recovered28==[p%28 for p in plain]
    assert result['positive_controls']['raw']['observed_max']>=round(ioc(plain,29),6)
    assert result['positive_controls']['chain']['observed_max']>=round(ioc(recovered28,28),6)
    for ctl in result['positive_controls'].values():
        assert ctl['passes_95th'] and ctl['exceedances']==0
        assert len(ctl['shuffle_maxima'])==99
    # Complemented output preserves IoC for every alphabet value and key.
    for c in range(29):
        for k in range(29):
            assert ((28-c-k)%29)==(28-((c+k)%29))%29
    for delta in range(1,29):
        forward=(delta-1)%28
        reverse=((29-delta)-1)%28
        assert reverse==27-forward
    # Source solved-text arm: compare each printed rounded IoC and offset.
    found=0
    for line in (source/'results/tests4.txt').read_text(encoding='utf-8').splitlines():
        m=re.search(r'^\s+(p\d+-\d+)\s+best ioc=([0-9.]+) off=(\d+) sign=(-?\d+)',line)
        if not m:
            continue
        section,score,offset,sign=m.groups()
        top=result['source_solved_running_key'][section]['top']
        assert (score,int(offset),int(sign))==(f"{top['ioc']:.3f}",top['offset'],top['sign'])
        found+=1
    assert found==9
    for section,row in result['sections'].items():
        assert len(row['shuffle_maxima'])==99
        assert row['selected_grid_tail']==(row['shuffle_exceedances']+1)/100
        assert 0<=row['shuffle_exceedances']<=99
        assert set(row['source_arms'])==set(ARMS)
    print('source bytes, 135 source top rows, nine solved-key rows, planted recovery and mirror identities match')


if __name__=='__main__':
    main()
