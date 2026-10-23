"""Independent arithmetic check of the post-target mixed 11-slot selection."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import check

H = Path(__file__).resolve().parent
N = 29


def enc(plain, mode, order, arms):
    key = arms['initial_key_state'][:order]
    factors = arms['recurrence_coefficients'][:order]
    for _ in range(order,len(plain)):
        key.append(sum(factors[j]*key[-order+j] for j in range(order)) % N)
    if mode=='sub':
        return [(p+k)%N for p,k in zip(plain,key)]
    if mode=='add':
        return [(p-k)%N for p,k in zip(plain,key)]
    return [(k-p)%N for p,k in zip(plain,key)]


def candidates(cipher, plan, pairs, triples):
    """Independent full eligible-candidate score inventory for one page."""
    found=[]
    for name, crib in plan['cribs'].items():
        n=len(crib)
        for mode in plan['modes']:
            for pos in range(len(cipher)-n-128+1):
                stream=check.key_for(cipher[pos:pos+n],crib,mode)
                polynomial, degree=check.connection(stream[:-2])
                if not 2<=degree<=min(5,(n-2)//2):
                    continue
                predicted=check.extend(stream[:-2],polynomial,n+128)
                if predicted[n-2:n]!=stream[-2:]:
                    continue
                decoded=check.decrypt(cipher[pos+n:pos+n+128],predicted[n:n+128],mode)
                val=sum(pairs.get((a,b),0) for a,b in zip(decoded,decoded[1:]))
                val+=5*sum((a,b,c) in triples for a,b,c in zip(decoded,decoded[1:],decoded[2:]))
                found.append((val,name,mode,pos,degree,decoded))
    return found


def main():
    grid=json.loads((H/'power-grid-plan.json').read_text(encoding='utf-8'))
    for name, expected in grid['frozen_inputs_sha256'].items():
        assert hashlib.sha256((H/name).read_bytes()).hexdigest()==expected, name
    plan=json.loads((H/'plan.json').read_text(encoding='utf-8'))
    inputs={x['page_id']:x['site_indices'] for x in json.loads((H/'inputs.json').read_text(encoding='utf-8'))['rows']}
    plain=json.loads((H/'power-input.json').read_text(encoding='utf-8'))['rune_indices']
    provenance=json.loads((H/'power-plan.json').read_text(encoding='utf-8'))['source']
    source_bytes=(H.parents[2]/provenance['path']).read_bytes()
    assert hashlib.sha256(source_bytes).hexdigest()==provenance['sha256']
    source=json.loads(source_bytes)
    source_control=next(x for x in source['controls'] if x['id']==provenance['reading_id'])
    source_page=next(x for x in source_control['decoded_pages'] if x['page']==provenance['page_id'])
    assert plain==source_page['rune_indices']
    arms=json.loads((H/'power-plan.json').read_text(encoding='utf-8'))['arms']
    old=json.loads((H/'results.json').read_text(encoding='utf-8'))['corrected']
    single={(r['mode'],r['order']):r for r in json.loads((H/'power-results.json').read_text(encoding='utf-8'))['rows']}
    result=json.loads((H/'power-grid-results.json').read_text(encoding='utf-8'))
    assert result['grid_plan_sha256']==hashlib.sha256((H/'power-grid-plan.json').read_bytes()).hexdigest()
    pairs={tuple(x['pair']):x['weight'] for x in plan['score']['bigrams']}
    triples={tuple(x) for x in plan['score']['trigrams']}
    other=[]
    total_windows=0
    for pid in grid['unchanged_pages_in_order']:
        page=check.corrected_page(inputs[pid],plan,pairs,triples)
        assert page==old[pid], pid
        scored=candidates(inputs[pid],plan,pairs,triples)
        assert len(scored)==page['verified_recurrences']
        other.extend(scored)
        total_windows+=page['windows']
    assert len(other)==result['unchanged_page_candidates']
    assert total_windows==result['unchanged_page_windows']
    for row in result['rows']:
        mode,order=row['mode'],row['order']
        cipher=enc(plain,mode,order,arms)
        page=check.corrected_page(cipher,plan,pairs,triples)
        scored=candidates(cipher,plan,pairs,triples)
        assert len(scored)==page['verified_recurrences']==row['planted_page_candidates']
        true=[x for x in scored if x[1:5]==('CIRCUMFERENCE',mode,52,order)]
        assert len(true)==1 and true[0][-1]==plain[65:193]
        value=true[0][0]
        all_scored=other+scored
        assert row['true_candidate_score']==value==single[(mode,order)]['true_candidate_score']
        assert row['true_candidate_global_rank']==1+sum(x[0]>value for x in all_scored)
        assert row['global_top_score_ties']==sum(x[0]==value for x in all_scored)
        assert row['all_11_page_candidates']==len(all_scored)
        assert row['all_11_page_windows']==total_windows+page['windows']
        assert row['global_rank_one'] and row['global_best_score']==value
    print(json.dumps({'unchanged_pages':10,'mixed_arms_checked':len(result['rows']),
                      'global_rank_one':sum(x['global_rank_one'] for x in result['rows']),
                      'result':'pass'}))


if __name__=='__main__':
    main()
