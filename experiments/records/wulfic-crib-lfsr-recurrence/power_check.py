"""Independent check of the post-target known-reading recovery and ranking."""
import hashlib
import json
from pathlib import Path

import check

H = Path(__file__).resolve().parent
plan = json.loads((H/'power-plan.json').read_text(encoding='utf-8'))
frozen = json.loads((H/'plan.json').read_text(encoding='utf-8'))
source_bytes = (H/'power-input.json').read_bytes()
assert hashlib.sha256(source_bytes).hexdigest() == plan['power_input_sha256']
old_bytes = (H/'results.json').read_bytes()
assert hashlib.sha256(old_bytes).hexdigest() == plan['frozen_results_sha256']
old = json.loads(old_bytes)
saved = json.loads((H/'power-results.json').read_text(encoding='utf-8'))
plain = json.loads(source_bytes)['rune_indices']
known_path = H.parents[2] / plan['source']['path']
known_bytes = known_path.read_bytes()
assert hashlib.sha256(known_bytes).hexdigest() == plan['source']['sha256']
known = json.loads(known_bytes)
known_row = next(x for x in known['controls'] if x['id'] == plan['source']['reading_id'])
known_page = next(x for x in known_row['decoded_pages'] if x['page'] == plan['source']['page_id'])
assert plain == known_page['rune_indices']
name = plan['crib']['name']
crib = frozen['cribs'][name]
offset = plan['crib']['offset']
start = offset + len(crib)
assert plain[offset:start] == crib and len(plain[start:start+128]) == 128
weights = {tuple(x['pair']):x['weight'] for x in frozen['score']['bigrams']}
triples = {tuple(x) for x in frozen['score']['trigrams']}


def score(values):
    return sum(weights.get((a,b),0) for a,b in zip(values,values[1:])) + 5*sum(
        (a,b,c) in triples for a,b,c in zip(values,values[1:],values[2:]))


def candidate_rows(cipher):
    out=[]
    for title,guess in frozen['cribs'].items():
        width=len(guess)
        for direction in frozen['modes']:
            for pos in range(len(cipher)-width-128+1):
                keypart=check.key_for(cipher[pos:pos+width],guess,direction)
                train=keypart[:-2]
                poly,degree=check.connection(train)
                if not 2<=degree<=min(5,len(train)//2):
                    continue
                prediction=check.extend(train,poly,width+128)
                if prediction[len(train):width] != keypart[-2:]:
                    continue
                following=check.decrypt(cipher[pos+width:pos+width+128],
                                        prediction[width:width+128],direction)
                out.append((title,direction,pos,degree,score(following),following))
    return out


assert saved['frozen_global_null_maximum'] == max(old['shared_null_maxima'])
assert saved['known_continuation_score'] == score(plain[start:start+128])
for item in saved['rows']:
    mode,order=item['mode'],item['order']
    state=plan['arms']['initial_key_state'][:order]
    coeff=plan['arms']['recurrence_coefficients'][:order]
    key=state[:]
    while len(key)<len(plain):
        key.append(sum(a*b for a,b in zip(coeff,key[-order:]))%29)
    if mode=='sub':
        cipher=[(p+k)%29 for p,k in zip(plain,key)]
    elif mode=='add':
        cipher=[(p-k)%29 for p,k in zip(plain,key)]
    else:
        cipher=[(k-p)%29 for p,k in zip(plain,key)]
    found=candidate_rows(cipher)
    true=[x for x in found if x[:4]==(name,mode,offset,order)]
    assert len(true)==1
    true_score=true[0][4]
    assert true[0][5]==plain[start:start+128]
    assert len(found)==item['eligible_candidates']
    assert true_score==item['true_candidate_score']==saved['known_continuation_score']
    assert 1+sum(x[4]>true_score for x in found)==item['true_rank']
    assert sum(x[4]==true_score for x in found)==item['score_ties']
    assert max(x[4] for x in found)==item['best_score']
    assert item['strong_power_gate'] == (item['known_128_exact'] and
        item['true_rank']==1 and true_score>saved['frozen_global_null_maximum'])
assert len(saved['rows'])==12
print('PASS independent known-reading power check: 12/12 exact continuations and score/rank comparisons')
