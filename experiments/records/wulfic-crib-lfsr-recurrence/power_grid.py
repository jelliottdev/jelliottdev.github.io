"""Post-target mixed 11-slot power check; original results stay read-only."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import run

HERE = Path(__file__).resolve().parent


def read_frozen(grid_plan: dict) -> dict:
    documents = {}
    for name, expected in grid_plan['frozen_inputs_sha256'].items():
        raw = (HERE / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected, name
        documents[name] = json.loads(raw)
    return documents


def plant(plain: list[int], mode: str, order: int, power_plan: dict) -> list[int]:
    key = power_plan['arms']['initial_key_state'][:order]
    coeff = power_plan['arms']['recurrence_coefficients'][:order]
    while len(key) < len(plain):
        key.append(sum(a*b for a,b in zip(coeff, key[-order:])) % 29)
    if mode == 'sub':
        return [(p+k) % 29 for p,k in zip(plain,key)]
    if mode == 'add':
        return [(p-k) % 29 for p,k in zip(plain,key)]
    return [(k-p) % 29 for p,k in zip(plain,key)]


def generate() -> dict:
    grid_plan = json.loads((HERE/'power-grid-plan.json').read_text(encoding='utf-8'))
    docs = read_frozen(grid_plan)
    plan = docs['plan.json']
    power_plan = docs['power-plan.json']
    original = docs['results.json']['corrected']
    power_rows = {(x['mode'],x['order']): x for x in docs['power-results.json']['rows']}
    inputs = {x['page_id']:x['site_indices'] for x in docs['inputs.json']['rows']}
    plain = docs['power-input.json']['rune_indices']
    assert len(plain) == grid_plan['replacement']['known_runes']
    assert len(inputs[grid_plan['replacement']['original_page']]) == grid_plan['replacement']['original_runes']
    crib_name = grid_plan['replacement']['crib']
    offset = grid_plan['replacement']['crib_offset']
    crib = plan['cribs'][crib_name]
    assert plain[offset:offset+len(crib)] == crib
    assert len(grid_plan['unchanged_pages_in_order']) == 10
    pairs,trips = run.plan_scoring(plan)
    unchanged = {}
    for pid in grid_plan['unchanged_pages_in_order']:
        found = run.cases(inputs[pid],plan['cribs'],pairs,trips)
        assert found == original[pid], pid
        unchanged[pid] = found
    unchanged_windows = sum(x['windows'] for x in unchanged.values())
    unchanged_candidates = sum(x['verified_recurrences'] for x in unchanged.values())
    unchanged_best = max(((pid,x['best']) for pid,x in unchanged.items() if x['best']),
                         key=lambda x:x[1]['score'])
    rows = []
    for mode in power_plan['arms']['modes']:
        for order in power_plan['arms']['orders']:
            cipher = plant(plain,mode,order,power_plan)
            planted = run.cases(cipher,plan['cribs'],pairs,trips)
            saved = power_rows[(mode,order)]
            assert planted['verified_recurrences'] == saved['eligible_candidates']
            assert planted['best']['score'] == saved['best_score']
            inferred = run.infer(cipher,crib,offset,mode)
            assert inferred is not None and inferred[1] == order
            start = offset+len(crib)
            recovered = run.decrypt(cipher[start:start+128],inferred[0],mode)
            true_score = run.score(recovered,pairs,trips)
            assert recovered == plain[start:start+128]
            assert true_score == saved['true_candidate_score']
            higher_other = sum(x['verified_recurrences'] for x in unchanged.values()
                               if x['best'] and x['best']['score'] > true_score)
            # Per-page best strictly below the true score proves every candidate
            # on that page is below it; equality likewise needs page inspection.
            assert all(x['best'] is None or x['best']['score'] < true_score
                       for x in unchanged.values())
            assert higher_other == 0
            row = {'mode':mode,'order':order,
                   'planted_page_runes':len(cipher),
                   'planted_page_windows':planted['windows'],
                   'planted_page_candidates':planted['verified_recurrences'],
                   'all_11_page_windows':planted['windows']+unchanged_windows,
                   'all_11_page_candidates':planted['verified_recurrences']+unchanged_candidates,
                   'true_candidate_score':true_score,
                   'true_candidate_exact_128':True,
                   'true_candidate_global_rank':saved['true_rank'],
                   'global_top_score_ties':saved['score_ties'],
                   'global_best_page':grid_plan['replacement']['known_page'],
                   'global_best_score':planted['best']['score'],
                   'higher_than_unchanged_best':true_score>unchanged_best[1]['score'],
                   'global_rank_one':saved['true_rank']==1}
            rows.append(row)
    return {'schema':'wulfic-crib-lfsr-posttarget-mixed-grid-v1',
            'grid_plan_sha256':hashlib.sha256((HERE/'power-grid-plan.json').read_bytes()).hexdigest(),
            'replaced_page':grid_plan['replacement'],
            'unchanged_pages':grid_plan['unchanged_pages_in_order'],
            'unchanged_page_windows':unchanged_windows,
            'unchanged_page_candidates':unchanged_candidates,
            'unchanged_page_best':{'page':unchanged_best[0],
                                   'score':unchanged_best[1]['score']},
            'rows':rows,
            'interpretation':'Post-target clean known-message power check; old 199 shuffles are not a mixed-grid null.'}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    computed=generate()
    output=HERE/'power-grid-results.json'
    if args.check:
        assert computed == json.loads(output.read_text(encoding='utf-8'))
    else:
        output.write_text(json.dumps(computed,ensure_ascii=False,indent=2)+'\n',
                          encoding='utf-8',newline='\n')
    print('mixed-grid rank one',sum(x['global_rank_one'] for x in computed['rows']),
          '/',len(computed['rows']))
