"""Frozen-fixture exact parity, key-read and timing harness; no source edits."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

from beam_shared import beam_decode as shared_decode

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT.parent/'source-cache/dukotah-cicada3301/liber-primus'
sys.path.insert(0,str(SOURCE/'analysis/campaign18_skip'))
import skipdecode as sk


class ObservedKey(list):
    def __init__(self, values, native_length, reads=None):
        super().__init__(values)
        self.native_length=native_length
        self.reads=reads if reads is not None else {'read_count':0,'max_read_index':-1,
                                                    'padded_read_count':0,'extension_count':0}
    def __add__(self, other):
        self.reads['extension_count']+=1
        return ObservedKey(list.__add__(self,other),self.native_length,self.reads)
    def __getitem__(self,item):
        if isinstance(item,int):
            self.reads['read_count']+=1
            self.reads['max_read_index']=max(self.reads['max_read_index'],item)
            self.reads['padded_read_count']+=item>=self.native_length
        return list.__getitem__(self,item)


def load_source():
    pinned=json.loads((HERE/'fixture-plan.json').read_text(encoding='utf-8'))
    path=SOURCE/'analysis/campaign18_skip/skipdecode.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==pinned['source_sha256']
    return pinned


def freeze_matrix():
    load_source()
    rng=random.Random(3301)
    rows=[]
    for i in range(32):
        length=rng.randrange(2,321)
        short=rng.randrange(3)==0
        rows.append({'id':f'matrix-{i:02d}','type':'random','length':length,
                     'key_length':rng.randrange(1,20) if short else 5*length+32,
                     'seed':rng.randrange(2**31),'sign':rng.choice([-1,1]),
                     'offset':rng.randrange(8),'beam_width':rng.choice([1,2,10,20,100]),
                     'max_skip':rng.randrange(5),'atbash':bool(rng.randrange(2))})
    path=HERE/'matrix.json'
    if path.exists():
        assert rows==json.loads(path.read_text(encoding='utf-8'))['cases']
    else:
        path.write_text(json.dumps({'schema':'beam-prefix-sharing-fixed-matrix-v1',
                                    'cases':rows},indent=2)+'\n',encoding='utf-8',newline='\n')
    print('frozen',len(rows),'extra cases',hashlib.sha256(path.read_bytes()).hexdigest())


def arrays(spec):
    n=spec['length']; seed=spec['seed']
    if spec['type']=='english':
        phrase='THE PRIMES ARE SACRED AND THE CIRCUMFERENCE REVEALS THE PILGRIM'
        source=sk.eng_to_idx(phrase*(n+1))
        cipher=source[:n]
    elif spec['type']=='zeros':
        cipher=[0]*n
    elif spec['type']=='constant':
        cipher=[seed%29]*n
    else:
        rng=random.Random(seed)
        cipher=[rng.randrange(29) for _ in range(n)]
    if spec['atbash']:
        cipher=[(28-c)%29 for c in cipher]
    if spec['type'] in ('zeros','constant'):
        key=[0 if spec['type']=='zeros' else seed%29]*spec['key_length']
    else:
        rng=random.Random(seed+1984)
        key=[rng.randrange(29) for _ in range(spec['key_length'])]
    return cipher,key


def pair(spec):
    C,K=arrays(spec)
    kwargs={k:spec[k] for k in ('sign','offset','beam_width','max_skip')}
    kwargs['o']=kwargs.pop('offset')
    kwargs['beam_w']=kwargs.pop('beam_width')
    native=len(K)
    key1=ObservedKey(K,native)
    start=time.perf_counter()
    expected=sk.beam_decode(C,key1,**kwargs)
    source_time=time.perf_counter()-start
    key2=ObservedKey(K,native)
    start=time.perf_counter()
    got=shared_decode(C,key2,gp=sk.gp,Q=sk.Q,**kwargs)
    shared_time=time.perf_counter()-start
    assert expected.keys()==got.keys(),spec['id']
    for field in expected:
        if expected[field]!=got[field]:
            raise AssertionError((spec['id'],field,expected[field] if field not in ('plain_idx','translit') else str(expected[field])[:60],got[field] if field not in ('plain_idx','translit') else str(got[field])[:60]))
    assert key1.reads==key2.reads,(spec['id'],key1.reads,key2.reads)
    return {'id':spec['id'],'length':len(C),'source_seconds':source_time,
            'shared_seconds':shared_time,'read_stats':key1.reads,
            'score':expected['score'],'beam_score':expected['beam_score'],
            'path_sha256':hashlib.sha256(bytes(expected['plain_idx'])).hexdigest()}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--freeze-matrix',action='store_true')
    ap.add_argument('--verify',action='store_true')
    ap.add_argument('--full',action='store_true')
    args=ap.parse_args()
    if args.freeze_matrix:
        freeze_matrix();return
    plan=load_source()
    matrix_path=HERE/'matrix.json'
    assert matrix_path.exists(), 'freeze matrix before comparisons'
    cases=plan['fixtures']+json.loads(matrix_path.read_text(encoding='utf-8'))['cases']
    if args.full:
        cases.append({'id':'full-12956','type':'english','length':12956,
                      'key_length':12956+512,'seed':3301,'sign':-1,'offset':0,
                      'beam_width':400,'max_skip':3,'atbash':False})
    rows=[pair(spec) for spec in cases]
    data={'schema':'beam-prefix-sharing-parity-v1',
          'fixture_plan_sha256':hashlib.sha256((HERE/'fixture-plan.json').read_bytes()).hexdigest(),
          'matrix_sha256':hashlib.sha256(matrix_path.read_bytes()).hexdigest(),
          'source_sha256':plan['source_sha256'],'cases':len(rows),
          'median_source_seconds':statistics.median(x['source_seconds'] for x in rows),
          'median_shared_seconds':statistics.median(x['shared_seconds'] for x in rows),
          'rows':rows}
    output=HERE/('full-receipt.json' if args.full else 'short-receipt.json')
    if args.verify:
        previous=json.loads(output.read_text(encoding='utf-8'))
        for old,new in zip(previous['rows'],rows):
            for field in ('id','length','read_stats','score','beam_score','path_sha256'):
                assert old[field]==new[field],(old['id'],field)
    else:
        output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('exact parity',len(rows),'median seconds',data['median_source_seconds'],data['median_shared_seconds'])


if __name__=='__main__':
    main()
