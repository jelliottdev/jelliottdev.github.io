"""Frozen synthetic parity, known-reading controls and cost measurement only."""
import argparse
import hashlib
import json
import random
import struct
import time

import numpy as np

import engine as e


def fixture(length, kind):
    if kind=='constant':
        return np.zeros(length,dtype=np.int64)
    rng=random.Random(8413301)
    return np.array([rng.randrange(29) for _ in range(length)],dtype=np.int64)


def plant(pair,key,readings):
    reading='warning' if (pair[0]*29+pair[1])%2==0 else 'lp2-56'
    plain=readings[reading]
    first=None
    for seed in range(3301,3333):
        cipher,skips,used=e.encoder.encipher_keyskip(plain,key,sign=1,supp=.83,seed=seed)
        if first is None:
            first=max(skips)
        if max(skips)<=3:
            return plain,cipher,{'a':pair[0],'b':pair[1],'reading':reading,'eligible':True,
                                'seed':seed,'attempts':seed-3300,'initial_max_skip':first,
                                'skip_total':sum(skips),'skip_max':max(skips),'skips':skips,
                                'used_key_positions':used,'cipher':cipher}
    return plain,None,{'a':pair[0],'b':pair[1],'reading':reading,'eligible':False,
                       'attempts':32,'initial_max_skip':first,'final_max_skip':max(skips)}


def validate(plan):
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']


def benchmark(key,readings):
    sample=[list(key)[i*26] for i in range(32)]
    screen_times=[]
    full_times=[]
    for pair in sample:
        k=np.array(key[pair],dtype=np.int64)
        start=time.perf_counter()
        e.sweep.beam(fixture(50,'uniform'),k,1,0,50,60)
        screen_times.append(time.perf_counter()-start)
        plain,cipher,row=plant(pair,key[pair],readings)
        assert row['eligible']
        start=time.perf_counter()
        e.sweep.beam(np.array(cipher,dtype=np.int64),k,1,0,len(plain),200)
        full_times.append(time.perf_counter()-start)
    mean=sum(screen_times)/len(screen_times)
    result={'schema':'fibonacci-skip-benchmark-v1','samples':32,
            'uniform50_source_screen_seconds_mean':mean,'uniform50_source_screen_seconds_max':max(screen_times),
            'known_reading_source_full_seconds_mean':sum(full_times)/len(full_times),
            'known_reading_source_full_seconds_max':max(full_times),
            'projected92510screens_at_mean_seconds':mean*92510,
            'projected92510screens_at_sample_max_seconds':max(screen_times)*92510,
            'limitation':'Descriptive synthetic timings, not a bound or measured manuscript survival rate. Confirmations add cost.'}
    e.write(e.HERE/'benchmark.json',result)
    print(json.dumps(result,indent=2),flush=True)


def parity(key):
    aliases=json.loads((e.HERE/'aliases.json').read_text(encoding='utf8'))
    cipher=fixture(50,'uniform')
    canonical={pair:e.sweep.beam(cipher,np.array(k,dtype=np.int64),1,0,50,60) for pair,k in key.items()}
    digest=hashlib.sha256()
    start=time.perf_counter()
    for index,r in enumerate(aliases):
        original=e.sweep.beam(cipher,np.array(key[r['a'],r['b']],dtype=np.int64),r['sign'],r['offset'],50,60)
        mapped=canonical[r['canonical_a'],r['canonical_b']]
        assert original==mapped
        assert e.sweep.Q.score_norm(e.text(original))==e.sweep.Q.score_norm(e.text(mapped))
        digest.update(struct.pack('<I',index)+bytes(original))
    # Verify complete native outputs AND ordered retained terminal beams in full fixtures.
    observer=e.terminal_observer()
    full_rows=[]
    pairs=[(0,0),(1,0),(0,1),(1,1),(28,28),(13,21)]
    for pair in pairs:
        for kind in ['uniform','constant']:
            cipher=fixture(277,kind)
            original_key=key[pair]
            for sign in (-1,1):
                for offset in range(5):
                    mapped=(sign*original_key[offset]%29,sign*original_key[offset+1]%29)
                    k1=np.array(original_key,dtype=np.int64)
                    k2=np.array(key[mapped],dtype=np.int64)
                    original=e.sweep.beam(cipher,k1,sign,offset,277,200)
                    normalized=e.sweep.beam(cipher,k2,1,0,277,200)
                    assert original==normalized
                    left=observer(cipher,k1,sign,offset,277,200)
                    right=observer(cipher,k2,1,0,277,200)
                    assert [(score,pointer-offset,text,path) for score,pointer,text,path in left]==right
                    assert original==list(max(left,key=lambda x:x[0])[3])
                    full_rows.append({'a':pair[0],'b':pair[1],'sign':sign,'offset':offset,'fixture':kind,
                                      'terminal_hypotheses':len(left),'ordered_terminal_parity':True,
                                      'output_sha256':hashlib.sha256(bytes(original)).hexdigest()})
    result={'schema':'fibonacci-native-alias-parity-v1','preflight_plan_sha256':e.sha(e.HERE/'preflight-plan.json'),
            'fixture_seed':8413301,'native50_alias_comparisons':len(aliases),'native50_canonical_cached_calls':len(canonical),
            'native50_exact_paths_scores_match':True,'ordered50_fixture_digest':digest.hexdigest(),
            'full277_representative_comparisons':len(full_rows),'full277_ordered_terminal_parity':True,
            'full277_rows':full_rows,'elapsed_seconds':time.perf_counter()-start,
            'limitation':'Synthetic cipher fixtures only. Exhaustive finite generator proof supports untested manuscript ciphertexts; this receipt does not decode them.'}
    e.write(e.HERE/'parity-results.json',result)
    print('PASS parity:8410 native50 mappings;120 full277 mappings and ordered terminal states',flush=True)


def controls(key,readings):
    rows=[]
    start=time.perf_counter()
    for pair,k in key.items():
        plain,cipher,row=plant(pair,k,readings)
        if cipher is not None:
            # Independent direct inversion, key-skip constraints and exact initial state.
            assert row['used_key_positions'][0]==0
            for i,j in enumerate(row['used_key_positions']):
                assert (cipher[i]+k[j])%29==plain[i]
                if i:
                    for rejected in range(row['used_key_positions'][i-1]+1,j):
                        assert (plain[i]-k[rejected])%29==cipher[i-1]
            array=np.array(k,dtype=np.int64)
            short=e.sweep.beam(np.array(cipher,dtype=np.int64),array,1,0,50,60)
            full=e.sweep.beam(np.array(cipher,dtype=np.int64),array,1,0,len(plain),200)
            ss=e.sweep.Q.score_norm(e.text(short))
            fs=e.sweep.Q.score_norm(e.text(full))
            row.update(screen_exact=short==plain[:50],full_exact=full==plain,
                       screen_score=ss,full_score=fs,screen_pass=ss>-6.5,full_pass=fs>-5.5,
                       both_gates_pass=ss>-6.5 and fs>-5.5,
                       returned_indices=full,returned_sha256=hashlib.sha256(bytes(full)).hexdigest())
        rows.append(row)
    eligible=[r for r in rows if r['eligible']]
    result={'schema':'fibonacci-all-canonical-key-controls-v1','preflight_plan_sha256':e.sha(e.HERE/'preflight-plan.json'),
            'cells':len(rows),'eligible':len(eligible),'no_eligible':len(rows)-len(eligible),
            'exact_complete_recovery':sum(r['full_exact'] for r in eligible),
            'exact_screen_recovery':sum(r['screen_exact'] for r in eligible),
            'screen_gate_pass':sum(r['screen_pass'] for r in eligible),
            'full_gate_pass':sum(r['full_pass'] for r in eligible),
            'both_gates_pass':sum(r['both_gates_pass'] for r in eligible),
            'zero_skip_plants':sum(r['skip_total']==0 for r in eligible),
            'elapsed_seconds':time.perf_counter()-start,'rows':rows,
            'limitation':'One fixed selected bounded-skip plant per canonical key; source score gates and exact recovery differ. Seed selection conditions on maxskip<=3. No full-search false-positive calibration.'}
    e.write(e.HERE/'control-results.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['benchmark','parity','controls'])
    mode=parser.parse_args().mode
    plan=json.loads((e.HERE/'preflight-plan.json').read_text(encoding='utf8'))
    validate(plan)
    key=e.keys()
    readings=json.loads((e.HERE/'known-readings.json').read_text(encoding='utf8'))
    if mode=='benchmark':
        benchmark(key,readings)
    elif mode=='parity':
        parity(key)
    else:
        controls(key,readings)


if __name__=='__main__':
    main()
