"""Untracked native-list throughput after exact parity gate, no source mutation."""
from __future__ import annotations

import hashlib
import json
import statistics
import time
from pathlib import Path

import validate
from beam_shared import beam_decode as shared_decode

H=Path(__file__).resolve().parent


def main():
    plan=validate.load_source()
    parity=json.loads((H/'full-receipt.json').read_text(encoding='utf-8'))
    assert parity['cases']==46 and parity['rows'][-1]['id']=='full-12956'
    assert parity['fixture_plan_sha256']==hashlib.sha256((H/'fixture-plan.json').read_bytes()).hexdigest()
    specs=json.loads((H/'fixture-plan.json').read_text(encoding='utf-8'))['fixtures']
    specs=[(next(x for x in specs if x['id']=='english-120'),30),
           (next(x for x in specs if x['id']=='english-400'),5),
           ({'id':'full-12956','type':'english','length':12956,'key_length':12956+512,
             'seed':3301,'sign':-1,'offset':0,'beam_width':400,'max_skip':3,'atbash':False},1)]
    rows=[]
    for spec,n in specs:
        C,K=validate.arrays(spec)
        kwargs={'sign':spec['sign'],'o':spec['offset'],'beam_w':spec['beam_width'],
                'max_skip':spec['max_skip']}
        a=validate.sk.beam_decode(C,K,**kwargs)
        b=shared_decode(C,K,gp=validate.sk.gp,Q=validate.sk.Q,**kwargs)
        assert a==b
        old,new=[],[]
        for iteration in range(n):
            sequence=('source','shared') if iteration%2==0 else ('shared','source')
            for implementation in sequence:
                t=time.perf_counter()
                if implementation=='source':
                    out=validate.sk.beam_decode(C,K,**kwargs)
                else:
                    out=shared_decode(C,K,gp=validate.sk.gp,Q=validate.sk.Q,**kwargs)
                sec=time.perf_counter()-t
                assert out==a
                (old if implementation=='source' else new).append(sec)
        rows.append({'id':spec['id'],'length':len(C),'repeats':n,
                     'source_median_seconds':statistics.median(old),
                     'shared_median_seconds':statistics.median(new),
                     'speedup_ratio':statistics.median(old)/statistics.median(new),
                     'source_seconds':old,'shared_seconds':new})
        print(rows[-1]['id'],rows[-1]['speedup_ratio'],flush=True)
    result={'schema':'beam-prefix-sharing-native-list-benchmark-v1',
            'source_sha256':plan['source_sha256'],
            'full_parity_receipt_sha256':hashlib.sha256((H/'full-receipt.json').read_bytes()).hexdigest(),
            'rows':rows,
            'limits':'Paired serial native-list benchmark on one Windows host; source and prototype outputs compared exactly; no production B04 runner changed.'}
    (H/'benchmark.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':
    main()
