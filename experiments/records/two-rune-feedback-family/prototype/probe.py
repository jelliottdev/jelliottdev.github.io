"""Synthetic/known-input source parity, aliases, power and runtime only; no targets."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import time
import numpy as np
import engine as e

HERE=Path(__file__).resolve().parent


def save(name,value):
    with (HERE/name).open('x',encoding='utf-8',newline='\n') as out:out.write(json.dumps(value,indent=2)+'\n')


def main():
    p=json.loads((HERE/'proposal-frozen.json').read_bytes())
    for row in p['files']:
        assert hashlib.sha256((HERE/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    manifest=json.loads((HERE/'source-manifest.json').read_bytes())
    for row in manifest['files']:
        assert hashlib.sha256((HERE/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
    model=e.setup();functions=model[0]
    known=json.loads((HERE/'known-readings.json').read_bytes())
    warning=next(x for x in known['controls'] if x['id']=='warning')['decoded_pages'][0]['rune_indices']
    texts=[('source-control',e.control.eng_to_idx(e.control.PLAIN)),('warning',warning)]
    rng=random.Random(p['synthetic_seed'])
    synthetic=np.array([rng.randrange(29) for _ in range(61)],dtype=np.int64)
    rows=[];started=time.perf_counter()
    for fi,name in enumerate(e.FUNCTIONS):
        for mixed in (0,1):
            source='mix' if mixed else 'pt'
            for sign in (-1,1):
                for reverse in (False,True):
                    cipher=synthetic[::-1].copy() if reverse else synthetic
                    scores=e.grid(cipher,fi,mixed,sign,*model)
                    max_error=0.0;arrays_exact=True
                    for a in range(29):
                        for b in range(29):
                            expected=e.source.decode(cipher.tolist(),e.source.F_BASIS[name],2,[a,b],source=source,sign=sign)
                            actual=e.decode(cipher,a,b,fi,mixed,sign,functions).tolist()
                            arrays_exact=arrays_exact and expected==actual
                            max_error=max(max_error,abs(e.source.score_norm(expected[2:])-float(scores[a*29+b])))
                    assert arrays_exact and max_error<=1e-12,(name,source,sign,reverse,max_error)
                    controls=[]
                    for label,plain0 in texts:
                        # A direction selects the target's input order; plant the known
                        # plaintext in decoder order, then reverse its external ciphertext
                        # for the reversed branch. Both calls must recover known text.
                        for primer in p['primers']:
                            cipher0=e.source.encipher(plain0,e.source.F_BASIS[name],2,primer,source=source,sign=sign)
                            external=cipher0[::-1] if reverse else cipher0
                            oriented=external[::-1] if reverse else external
                            ciphertext=np.asarray(oriented,dtype=np.int64)
                            outcomes=e.grid(ciphertext,fi,mixed,sign,*model)
                            actual=e.decode(ciphertext,*primer,fi,mixed,sign,functions).tolist()
                            native=e.source.decode(oriented,e.source.F_BASIS[name],2,primer,source=source,sign=sign)
                            assert actual==native
                            index=primer[0]*29+primer[1];truth=float(outcomes[index]);reference=e.source.score_norm(actual[2:])
                            assert abs(truth-reference)<=1e-12
                            higher=int(np.sum(outcomes>truth+1e-12));ties=int(np.sum(np.abs(outcomes-truth)<=1e-12))
                            exact=actual==plain0
                            chosen=int(np.argmax(outcomes));chosen_pair=list(divmod(chosen,29))
                            chosen_plain=e.decode(ciphertext,*chosen_pair,fi,mixed,sign,functions).tolist()
                            controls.append({'text':label,'primer':primer,'exact_supplied_key_recovery':exact,
                                             'truth_score':truth,'higher':higher,'ties_including_truth':ties,
                                             'best_score':float(np.max(outcomes)),
                                             'earliest_best_primer':chosen_pair,'earliest_best_complete_recovery':chosen_plain==plain0,
                                             'earliest_best_scored_tail_recovery':chosen_plain[2:]==plain0[2:],
                                             'search_gate_pass':bool(exact and higher==0 and ties==1 and truth>=-5.5)})
                    timings=[]
                    for length in p['benchmark_lengths']:
                        for pattern in ('random','long-label'):
                            c=np.array([rng.randrange(29) for _ in range(length)] if pattern=='random' else [28]*length,dtype=np.int64)
                            e.grid(c,fi,mixed,sign,*model)
                            samples=[]
                            for _ in range(p['benchmark_repeats']):
                                start=time.perf_counter();e.grid(c,fi,mixed,sign,*model);samples.append(time.perf_counter()-start)
                            timings.append({'length':length,'pattern':pattern,'samples':samples,'worst_seconds_per_rune':max(samples)/length})
                    rows.append({'function':name,'source':source,'sign':sign,'direction':'reverse' if reverse else 'forward',
                                 'synthetic_parity_arrays':841,'synthetic_arrays_exact':arrays_exact,'maximum_score_error':max_error,
                                 'controls':controls,'search_controls_passed':sum(x['search_gate_pass'] for x in controls),
                                 'benchmark':timings,'projected_seconds_50whole_searches':max(x['worst_seconds_per_rune'] for x in timings)*12956*50})
                    print(name,source,sign,'rev' if reverse else 'fwd','controls',rows[-1]['search_controls_passed'],'/6','projection',round(rows[-1]['projected_seconds_50whole_searches'],2),flush=True)
    # Exhaustive pair truth tables prove signed-function equivalence, independent of C.
    classes={};aliases=[]
    for fi,name in enumerate(e.FUNCTIONS):
        for sign in (-1,1):
            signature=((sign*functions[fi])%29).astype(np.uint8).tobytes()
            digest=hashlib.sha256(signature).hexdigest();classes.setdefault(digest,[]).append({'function':name,'sign':sign})
    for members in classes.values():
        if len(members)>1:aliases.append(members)
    # Check sign/seed relabelling of each proved function alias on all841 states.
    checked=0
    for group in aliases:
        left,right=group
        li=e.FUNCTIONS.index(left['function']);ri=e.FUNCTIONS.index(right['function'])
        for mixed in (0,1):
            for reverse in (False,True):
                cipher=synthetic[::-1].copy() if reverse else synthetic
                for a in range(29):
                    for b in range(29):
                        mapped=[left['sign']*right['sign']*a%29,left['sign']*right['sign']*b%29]
                        assert np.array_equal(e.decode(cipher,a,b,li,mixed,left['sign'],functions),e.decode(cipher,*mapped,ri,mixed,right['sign'],functions))
                        checked+=1
    save('prototype-results.json',{'plan_sha256':hashlib.sha256((HERE/'proposal-frozen.json').read_bytes()).hexdigest(),
                                  'target_data_loaded_or_scored':False,'branches':rows,'signed_function_classes':len(classes),
                                  'function_alias_groups':aliases,'synthetic_alias_array_comparisons':checked,
                                  'all56_projected_seconds_50whole_searches':sum(x['projected_seconds_50whole_searches'] for x in rows),
                                  'seconds':time.perf_counter()-started})


if __name__=='__main__':main()
