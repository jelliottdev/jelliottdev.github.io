"""Fixed known-reading plants for all112 distinct signed ramp arrays."""
import hashlib
import json
import random
import time

import numpy as np

import engine as e


def main():
    plan=json.loads((e.HERE/'control-plan.json').read_text(encoding='utf8'))
    for item in plan['inputs']:
        assert e.sha(e.ROOT/item['path'])==item['sha256'],item['path']
    manifest=json.loads((e.HERE/'key-manifest.json').read_text(encoding='utf8'))
    readings=json.loads((e.HERE/'known-readings.json').read_text(encoding='utf8'))
    rows=[]
    for rep in manifest['signed_control_representatives']:
        key=e.source.page_seeded_stream(rep['source_index'],1124,rep['mode'])
        assert hashlib.sha256(bytes(key)).hexdigest()==rep['key_sha256']
        plain=readings[rep['reading']]
        cipher,skips,used=e.encoder.encipher_keyskip(plain,key,sign=rep['sign'],supp=.83,seed=3301)
        assert max(skips)<=1
        # Independent encryption/skip recount, and source Atbash involution.
        rng=random.Random(3301)
        p=0
        previous=None
        rebuilt=[]
        rebuilt_skips=[]
        for value in plain:
            rejected=0
            while True:
                c=(value-rep['sign']*key[p])%29
                if previous is not None and c==previous and rng.random()<.83:
                    p+=1
                    rejected+=1
                else:
                    break
            rebuilt.append(c)
            rebuilt_skips.append(rejected)
            previous=c
            p+=1
        assert rebuilt==cipher and rebuilt_skips==skips
        array=np.array(cipher,dtype=np.int64)
        assert e.source._atbash(e.source._atbash(array)).tolist()==cipher
        karray=np.array(key,dtype=np.int64)
        start=time.perf_counter()
        short=e.sweep.beam(array,karray,rep['sign'],0,50,60)
        short_time=time.perf_counter()-start
        start=time.perf_counter()
        full=e.sweep.beam(array,karray,rep['sign'],0,len(plain),300)
        full_time=time.perf_counter()-start
        ss=e.sweep.Q.score_norm(e.text(short))
        fs=e.sweep.Q.score_norm(e.text(full))
        rows.append(rep|{'seed':3301,'attempts':1,'eligible':True,'skip_total':sum(skips),'skip_max':max(skips),
                         'skips':skips,'used_key_positions':used,'cipher':cipher,
                         'screen_indices':short,'full_indices':full,
                         'screen_score':ss,'full_score':fs,'screen_pass':ss>-6.5,'full_pass':fs>-5.5,
                         'both_gates_pass':ss>-6.5 and fs>-5.5,'screen_exact':short==plain[:50],'full_exact':full==plain,
                         'full_sha256':hashlib.sha256(bytes(full)).hexdigest(),
                         'screen_seconds':short_time,'full_seconds':full_time})
    assert len(rows)==112
    signatures={(r['signed_slope'],r['reading'],tuple(r['skips']),tuple(r['screen_indices']),tuple(r['full_indices'])) for r in rows}
    receipt={'schema':'page-ramp-controls-v1','control_plan_sha256':e.sha(e.HERE/'control-plan.json'),
             'signed_array_plants':112,'structural_slope_reading_problems':len(signatures),
             'eligible':112,'no_eligible':0,'fixed_seed':3301,'resampling':False,
             'genuine_skip_plants':sum(r['skip_total']>0 for r in rows),'zero_skip_plants':sum(r['skip_total']==0 for r in rows),
             'exact_screen_recovery':sum(r['screen_exact'] for r in rows),
             'exact_complete_recovery':sum(r['full_exact'] for r in rows),
             'screen_gate_passes':sum(r['screen_pass'] for r in rows),
             'full_gate_passes':sum(r['full_pass'] for r in rows),
             'both_gate_passes':sum(r['both_gates_pass'] for r in rows),
             'screen_seconds_mean':sum(r['screen_seconds'] for r in rows)/112,
             'full_seconds_mean':sum(r['full_seconds'] for r in rows)/112,
             'projected660screens_at_measured_mean_seconds':660*sum(r['screen_seconds'] for r in rows)/112,
             'rows':rows,'limit':'112array checks represent only8slope/reading structures under cipher translation; not112independent power samples. Timing descriptive, score gates not exact recovery or a global-null calibration.'}
    e.write(e.HERE/'control-results.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k!='rows'},indent=2),flush=True)


if __name__=='__main__':
    main()
