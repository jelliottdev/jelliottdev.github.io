"""Two frozen actual-LP2 Stage D fixture parity and separate RSS profiling."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

import psutil
from beam_shared import beam_decode as fast_decode

H=Path(__file__).resolve().parent
ROOT=H.parents[2]
SOURCE_ROOT=ROOT.parent/'source-cache/dukotah-cicada3301'
HELPER=ROOT/'research/performance/b04-stage-b-2026-10-23/resumable_d_pre_optional.py'


def load_inputs():
    plan=json.loads((H/'stage-d-plan.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(HELPER.read_bytes()).hexdigest()==plan['stage_d_helper_sha256']
    spec=importlib.util.spec_from_file_location('stage_d_parity_helper',HELPER)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    api, _, ks, sk, hashes=helper.R.load_source(SOURCE_ROOT)
    assert helper.R.PIN==plan['source_revision'] and hashes==plan['source_hashes']
    name,c0,c1=api.full_unsolved()
    assert name==plan['segment_name'] and len(c0)==len(c1)==plan['segment_runes']
    assert hashlib.sha256(bytes(c0)).hexdigest()==plan['cipher_sha256']['c0']
    assert hashlib.sha256(bytes(c1)).hexdigest()==plan['cipher_sha256']['c1']
    return plan,helper,api,ks,sk,c0,c1


def prepare(stage, inputs):
    plan,helper,api,ks,sk,c0,c1=inputs
    arm=next(x for x in plan['arms'] if x['stage']==stage)
    merged=ROOT.parent/f'b04-lp2-{stage}-20261023/merged.json'
    assert hashlib.sha256(merged.read_bytes()).hexdigest()==arm['merged_sha256']
    row=json.loads(merged.read_text(encoding='utf-8'))['source_stage_summary']['top50'][0]
    assert row==arm['selected_row']
    native_length=len(c0)+int(row.get('offset',0) or 0)+512
    assert native_length==arm['native_requested_length']
    key=ks.make_ks(row['gen'],row['red'],bytes.fromhex(row['seed_hex']),native_length)
    if row['dir']=='rev':
        key=key[::-1]
    assert len(key)==arm['native_actual_length']
    assert hashlib.sha256(bytes(key)).hexdigest()==arm['native_key_sha256']
    cipher=c0 if row['atbash']==0 else c1
    kwargs={'sign':row['sign'],'o':row['offset'],'beam_w':api.BEAM_W,'max_skip':api.MAX_SKIP}
    assert kwargs['beam_w']==plan['beam_width'] and kwargs['max_skip']==plan['max_skip']
    return helper,sk,cipher,key,kwargs


def once(stage,implementation,profile_memory=False):
    helper,sk,cipher,key,kwargs=prepare(stage,load_inputs())
    observed=helper.ObservedKey(key,len(key))
    process=psutil.Process()
    baseline=process.memory_info().rss
    peak=[baseline]
    done=threading.Event()
    def sample():
        while not done.wait(0.005):
            peak[0]=max(peak[0],process.memory_info().rss)
    worker=threading.Thread(target=sample,daemon=True)
    if profile_memory:
        worker.start()
    t=time.perf_counter()
    try:
        if implementation=='source':
            result=sk.beam_decode(cipher,observed,**kwargs)
        else:
            result=fast_decode(cipher,observed,gp=sk.gp,Q=sk.Q,**kwargs)
    finally:
        done.set()
        if profile_memory:
            worker.join()
    seconds=time.perf_counter()-t
    peak[0]=max(peak[0],process.memory_info().rss)
    receipt={'stage':stage,'implementation':implementation,'seconds':seconds,
             'score':result['score'],'beam_score':result['beam_score'],
             'ptr_end':result['ptr_end'],'runes':len(result['plain_idx']),
             'plain_sha256':hashlib.sha256(bytes(result['plain_idx'])).hexdigest(),
             'translit_sha256':hashlib.sha256(result['translit'].encode('utf-8')).hexdigest(),
             'key_reads':observed.reads,'native_key_length':len(key),
             'padding_branch_taken':observed.reads['extension_count']>0,
             'padded_zero_read':observed.reads['padded_read_count']>0}
    if profile_memory:
        receipt.update(rss_baseline=baseline,rss_peak=peak[0],rss_peak_delta=peak[0]-baseline)
    return result,receipt


def pair():
    rows=[]
    for stage in 'AB':
        original,a=once(stage,'source')
        optimized,b=once(stage,'fast')
        assert original.keys()==optimized.keys()
        assert original==optimized,stage
        for field in ('score','beam_score','ptr_end','runes','plain_sha256',
                      'translit_sha256','key_reads','native_key_length',
                      'padding_branch_taken','padded_zero_read'):
            assert a[field]==b[field],(stage,field)
        rows.append({'stage':stage,'source':a,'fast':b,
                     'exact_all_return_fields':True,'exact_key_access':True})
        print('PASS',stage,'full returned dict and key reads',flush=True)
    output={'schema':'beam-prefix-sharing-b04-stage-d-parity-v1',
            'plan_sha256':hashlib.sha256((H/'stage-d-plan.json').read_bytes()).hexdigest(),
            'rows':rows,'status':'Experimental representation only; official Stage D untouched.'}
    (H/'stage-d-parity.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8',newline='\n')


def memory():
    # Each decoder gets a fresh process, separating peak RSS from timing runs.
    rows=[]
    for implementation in ('source','fast'):
        command=[sys.executable,str(Path(__file__).resolve()),'--memory-child',implementation]
        response=subprocess.run(command,check=True,capture_output=True,text=True)
        rows.append(json.loads(response.stdout))
    for field in ('score','beam_score','ptr_end','runes','plain_sha256','translit_sha256','key_reads'):
        assert rows[0][field]==rows[1][field],field
    output={'schema':'beam-prefix-sharing-stage-d-rss-v1',
            'plan_sha256':hashlib.sha256((H/'stage-d-plan.json').read_bytes()).hexdigest(),
            'method':'Two fresh child processes, RSS polled every 5 ms; sample at completion also retained.',
            'rows':rows}
    (H/'stage-d-memory.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS independent process RSS',[(x['implementation'],x['rss_peak']) for x in rows])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--pair',action='store_true')
    parser.add_argument('--memory',action='store_true')
    parser.add_argument('--memory-child',choices=['source','fast'])
    args=parser.parse_args()
    if args.memory_child:
        _,receipt=once('A',args.memory_child,profile_memory=True)
        print(json.dumps(receipt))
    elif args.memory:
        memory()
    elif args.pair:
        pair()
    else:
        parser.error('select --pair or --memory')
