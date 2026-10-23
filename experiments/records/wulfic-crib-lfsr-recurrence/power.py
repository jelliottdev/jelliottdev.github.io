"""Post-target known-reading power check; frozen main results are read-only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run

H = Path(__file__).resolve().parent


def generate() -> dict:
    plan = json.loads((H/'power-plan.json').read_text(encoding='utf-8'))
    original = json.loads((H/'plan.json').read_text(encoding='utf-8'))
    input_bytes = (H/'power-input.json').read_bytes()
    assert hashlib.sha256(input_bytes).hexdigest() == plan['power_input_sha256']
    old_bytes = (H/'results.json').read_bytes()
    assert hashlib.sha256(old_bytes).hexdigest() == plan['frozen_results_sha256']
    old = json.loads(old_bytes)
    assert len(old['shared_null_maxima']) == 199
    null_high = max(x for x in old['shared_null_maxima'] if x is not None)
    plain = json.loads(input_bytes)['rune_indices']
    crib_name = plan['crib']['name']
    crib = original['cribs'][crib_name]
    offset = plan['crib']['offset']
    following_start = offset + len(crib)
    assert plain[offset:following_start] == crib
    target = plain[following_start:following_start+128]
    weights, triples = run.plan_scoring(original)
    rows = []
    for mode in plan['arms']['modes']:
        for order in plan['arms']['orders']:
            key = plan['arms']['initial_key_state'][:order]
            coefficients = plan['arms']['recurrence_coefficients'][:order]
            while len(key) < len(plain):
                key.append(sum(a*b for a,b in zip(coefficients,key[-order:])) % 29)
            if mode == 'sub':
                cipher = [(p+k)%29 for p,k in zip(plain,key)]
            elif mode == 'add':
                cipher = [(p-k)%29 for p,k in zip(plain,key)]
            else:
                cipher = [(k-p)%29 for p,k in zip(plain,key)]
            found = run.infer(cipher,crib,offset,mode)
            recovered = (run.decrypt(cipher[following_start:following_start+128],
                       found[0],mode) if found else [])
            true_score = run.score(recovered,weights,triples) if len(recovered)==128 else None
            all_scores = []
            for name, guess in original['cribs'].items():
                for direction in original['modes']:
                    for pos in range(len(cipher)-len(guess)-128+1):
                        item = run.infer(cipher,guess,pos,direction)
                        if item is None:
                            continue
                        output = run.decrypt(cipher[pos+len(guess):pos+len(guess)+128],
                                             item[0],direction)
                        all_scores.append({'score':run.score(output,weights,triples),
                                           'crib':name,'mode':direction,'pos':pos,
                                           'order':item[1]})
            whole = run.cases(cipher,original['cribs'],weights,triples)
            assert len(all_scores)==whole['verified_recurrences']
            assert max((x['score'] for x in all_scores),default=None)==(whole['best']['score'] if whole['best'] else None)
            matching = [x for x in all_scores if x['crib']==crib_name and
                        x['mode']==mode and x['pos']==offset and x['order']==order]
            assert len(matching)==1 and matching[0]['score']==true_score
            rank = 1+sum(x['score']>true_score for x in all_scores)
            tied = sum(x['score']==true_score for x in all_scores)
            exact = recovered==target
            strong = exact and rank==1 and true_score>null_high
            rows.append({'mode':mode,'order':order,'true_crib_offset':offset,
                         'true_candidate_score':true_score,
                         'known_128_exact':exact,
                         'eligible_candidates':len(all_scores),
                         'true_rank':rank,'score_ties':tied,
                         'best_score':whole['best']['score'] if whole['best'] else None,
                         'best_candidate':{k:v for k,v in whole['best'].items() if k!='continuation'} if whole['best'] else None,
                         'above_all_199_old_null_maxima':true_score>null_high,
                         'strong_power_gate':strong})
    return {'schema':'wulfic-crib-lfsr-posttarget-power-v1',
            'known_page':'lp1-14','known_reading':'second-koan',
            'frozen_global_null_maximum':null_high,
            'known_continuation_score':run.score(target,weights,triples),
            'rows':rows}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    calculated=generate()
    output=H/'power-results.json'
    if args.check:
        assert calculated==json.loads(output.read_text(encoding='utf-8'))
    else:
        output.write_text(json.dumps(calculated,ensure_ascii=False,indent=2)+'\n',
                          encoding='utf-8',newline='\n')
    print('known score',calculated['known_continuation_score'],
          'frozen null max',calculated['frozen_global_null_maximum'],
          'full recovery',sum(r['known_128_exact'] for r in calculated['rows']),
          'strong gate',sum(r['strong_power_gate'] for r in calculated['rows']))


if __name__=='__main__':
    main()
