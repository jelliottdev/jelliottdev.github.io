"""Independent index-map reconstruction of every route and first full control."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from math import ceil, isqrt
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
LATIN=['F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
       'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA']
COMMON={'THE','AND','FOR','ING','ION','THA','ENT','HER','WAS','HIS','ALL','BUT','ARE','NOT','YOU','CAN'}
COLUMN=COMMON|{'HAS','OUR','OUT'}
KEYS={'CABAL':[5,24,17,24,20],'DIVINITY':[23,10,1,10,9,10,16,26],
      'DEOR':[23,18,3,4],'SHADOWS':[15,8,24,23,3,7,15]}


def prime(value:int)->bool:
    return value>=2 and all(value%d for d in range(2,isqrt(value)+1))


def ioc(seq:list[int])->float:
    if len(seq)<2:return 0.0
    c=Counter(seq)
    return 29*sum(q*(q-1) for q in c.values())/(len(seq)*(len(seq)-1))


def trigrams(seq:list[int],allowed:set[str])->int:
    text=''.join(LATIN[x] for x in seq)
    return sum(text[i:i+3] in allowed for i in range(len(text)-2))


def route_indices(name:str, values:list[int], deor:list[int])->list[int|None]:
    n=len(values)
    if name=='prime_positions':return [i for i in range(n) if prime(i)]
    if name=='reversed':return list(range(n-1,-1,-1))
    if name.startswith('columnar_w'):
        width=int(name.split('w')[-1]); rows=ceil(n/width)
        return [i for c in range(width) for r in range(rows) if (i:=r*width+c)<n]
    if name.startswith('diagonal_w'):
        width=int(name.split('w')[-1]); rows=ceil(n/width)
        return [i for diagonal in range(width+rows-1) for r in range(rows)
                if 0<=diagonal-r<width and (i:=r*width+diagonal-r)<n]
    if name.startswith('spiral_w'):
        width=int(name.split('w')[-1]); height=ceil(n/width)
        top,bottom,left,right=0,height-1,0,width-1
        out=[]
        def add(r,c):
            if len(out)<n:
                position=r*width+c
                out.append(position if position<n else None)
        while top<=bottom and left<=right:
            for c in range(left,right+1):add(top,c)
            top+=1
            for r in range(top,bottom+1):add(r,right)
            right-=1
            if top<=bottom:
                for c in range(right,left-1,-1):add(bottom,c)
                bottom-=1
            if left<=right:
                for r in range(bottom,top-1,-1):add(r,left)
                left+=1
        return out[:n]
    if name=='gp_value_sorted':return sorted(range(n),key=lambda i:values[i])
    if name.startswith('every_'):
        parts=name.split('_')
        return list(range(int(parts[-1].replace('start','')),n,int(parts[1].replace('th',''))))
    if name=='fibonacci_positions':
        fib=[0,1]
        while fib[-1]<n:fib.append(fib[-1]+fib[-2])
        return [i for i in fib if i<n]
    if name.startswith('route_'):
        key=KEYS[name[len('route_'):]];width=len(key);rows=ceil(n/width)
        return [i for c in sorted(range(width),key=lambda c:key[c]) for r in range(rows) if (i:=r*width+c)<n]
    if name=='deor_transposition':return sorted(range(n),key=lambda i:(deor[i],i))
    raise ValueError(name)


def inspect(page:list[int],deor:list[int],names:list[str])->tuple[list[dict],int]:
    nonprime=[x for i,x in enumerate(page) if not prime(i)]
    result=[]; maximum=0
    for name in names:
        idx=route_indices(name,nonprime,deor)
        output=[nonprime[i] if i is not None else 0 for i in idx]
        allowed=COLUMN if name.startswith('columnar_w') else COMMON
        tri=trigrams(output,allowed)
        gate=5 if name.startswith(('columnar_w','diagonal_w','spiral_w')) else (3 if name.startswith('every_') else None)
        reported=gate is None or tri>gate
        maximum=max(maximum,tri)
        result.append({'name':name,'values':output,'trigrams':tri,'source_gate':gate,'reported':reported,
                       'ioc':ioc(output),'complete_permutation':len(output)==len(nonprime) and Counter(output)==Counter(nonprime)})
    return result,maximum


def verify()->None:
    plan_raw=(HERE/'plan.json').read_bytes();input_raw=(HERE/'inputs.json').read_bytes();gate_raw=(HERE/'gate.json').read_bytes()
    result=json.loads((HERE/'results.json').read_text(encoding='utf8'))
    source=json.loads((HERE/'source-run.json').read_text(encoding='utf8'))
    data=json.loads(input_raw)
    for name,raw in [('plan_sha256',plan_raw),('inputs_sha256',input_raw),('gate_sha256',gate_raw)]:
        assert result[name]==hashlib.sha256(raw).hexdigest()
    values=data['values'];deor=data['deor_key_prefix']
    assert len(values)==217 and len(deor)==170
    observed=result['observed']
    assert observed['prime_position_count']==47 and observed['nonprime_position_count']==170
    assert observed['prime_index_value_count']==65 and observed['nonprime_index_value_count']==152
    assert observed['best_shift']==0
    assert observed['nonprime_ioc']==ioc([x for i,x in enumerate(values) if not prime(i)])
    rows=observed['routes'];assert len(rows)==observed['route_count']==58
    names=[r['name'] for r in rows]
    independent,maximum=inspect(values,deor,names)
    assert maximum==observed['max_trigrams']
    assert sum(r['reported'] for r in independent)==observed['source_reported_count']==source['source_reported_count']
    assert set(source['source_reported_route_names'])=={r['name'] for r in independent if r['reported']}
    for saved,again in zip(rows,independent):
        for field in ('name','trigrams','source_gate','reported','ioc','complete_permutation'):
            assert saved[field]==again[field]
        assert saved['length']==len(again['values'])
        assert saved['first_40_values']==again['values'][:40]
        assert saved['decode_sha256']==hashlib.sha256(bytes(again['values'])).hexdigest()
    controls=result['controls'];assert controls['replicates']==len(controls['rows'])==199
    assert controls['max_trigram_exceedances']==sum(r['max_trigrams']>=maximum for r in controls['rows'])
    assert controls['reported_count_exceedances']==sum(r['source_reported_count']>=observed['source_reported_count'] for r in controls['rows'])
    rng=np.random.default_rng(controls['seed'])
    shuffled=rng.permutation(np.asarray(values,dtype=np.int16)).tolist()
    first,first_max=inspect(shuffled,deor,names)
    assert first_max==controls['rows'][0]['max_trigrams']
    assert sum(r['reported'] for r in first)==controls['rows'][0]['source_reported_count']
    print('Independent 58-route/digest reconstruction, source receipt and complete null-0 search passed.')


if __name__=='__main__':verify()
