"""Minimum column-balance score over all orders of four intact sections."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/lp1-section-order.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def partition():
    orders=list(permutations(range(4)))
    canonical=lambda o:min(o[i:]+o[:i] for i in range(4))
    representatives=sorted({canonical(o) for o in orders})
    membership=[representatives.index(canonical(o)) for o in orders]
    assert len(representatives)==6 and all(membership.count(i)==4 for i in range(6))
    return orders,representatives,membership

def score(values,k):
    total=sum(values)
    return sum((k*sum(values[j::k])-total)**2 for j in range(k))

def class_scores(groups,k,representatives):
    assert sum(map(len,groups))%k==0,'Cyclic reduction requires whole rows'
    return [score([x for s in order for x in groups[s]],k) for order in representatives]

def produce():
    assert sha(PLAN)=='270f19a833c614574ffc7d335905f9f1cd8adefaa9f4fc60b69c97aac775f349'
    plan=json.loads(PLAN.read_bytes())
    for item in plan['inputs']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    fixed_path=ROOT/'experiments/records/lp1-section-balance/results.json'
    fixed=json.loads(fixed_path.read_bytes())
    receipt=json.loads((ROOT/'experiments/records/lp1-section-balance/audit.json').read_bytes())
    assert sha(fixed_path)==receipt['report_sha256']
    ledger=json.loads((ROOT/'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    groups=[[w['rune_length'] for w in ledger if w['section']==s['id']] for s in plan['sections']]
    assert groups==fixed['section_lengths']
    orders,reps,membership=partition();observed=class_scores(groups,16,reps)
    all_observed=[score([x for s in order for x in groups[s]],16) for order in orders]
    assert all_observed==[observed[i] for i in membership]
    minimum=min(observed);rng=random.Random(plan['seed']);trials=[]
    for trial in range(plan['trials']):
        shuffled=[]
        for original in groups:
            section=original.copy();rng.shuffle(section);shuffled.append(section)
        scores=class_scores(shuffled,16,reps)
        assert scores[membership[0]]==fixed['null_integer_scores'][trial]
        low=min(scores)
        trials.append({'class_scores':scores,'minimum':low,
            'minimizing_order_indices':[i for i,c in enumerate(membership) if scores[c]==low]})
    tail=sum(t['minimum']<=minimum for t in trials)
    p=Fraction(tail+1,len(trials)+1)
    return {'plan_sha256':sha(PLAN),'producer_sha256':sha(Path(__file__)),
        'section_ids':[s['id'] for s in plan['sections']],'orders':orders,'class_representatives':reps,
        'order_class_indices':membership,'observed_class_scores':observed,'observed_order_scores':all_observed,
        'observed_minimum':minimum,'observed_minimizing_order_indices':[i for i,q in enumerate(all_observed) if q==minimum],
        'trials':trials,'trial_count':len(trials),'seed':plan['seed'],'lower_tail_with_ties':tail,
        'p_fraction':str(p),'p':float(p),'limits':'Selection among these 24 orders only; not the original exploratory search, intent or decryption.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output path')
    result=produce()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,separators=(',',':'));f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='trials'},indent=2))
