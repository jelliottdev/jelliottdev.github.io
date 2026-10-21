"""Independently evaluate all 24 section orders in every frozen null trial."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
RUNES=set('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def check(path):
    data=json.loads(path.read_bytes());plan_path=ROOT/'experiments/plans/lp1-section-order.json'
    assert sha(plan_path)==data['plan_sha256']=='270f19a833c614574ffc7d335905f9f1cd8adefaa9f4fc60b69c97aac775f349'
    assert sha(ROOT/'scripts/lp1_section_order.py')==data['producer_sha256']
    plan=json.loads(plan_path.read_bytes())
    for source in plan['inputs']:assert sha(ROOT/source['path'])==source['sha256']
    fixed_path=ROOT/'experiments/records/lp1-section-balance/results.json'
    fixed=json.loads(fixed_path.read_bytes())
    assert sha(fixed_path)==json.loads((fixed_path.parent/'audit.json').read_bytes())['report_sha256']
    ledger=json.loads((ROOT/'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    groups=[]
    for section in plan['sections']:
        raw=''.join((ROOT/f'text/{p}.txt').read_text(encoding='utf-8') for p in section['pages'])
        raw=''.join(c for c in raw if c not in '/\r\n');tokens=[];token=''
        for i,c in enumerate(raw):
            if c in RUNES:token+=c
            elif c=="'" and token and i+1<len(raw) and raw[i+1] in RUNES:token+=c
            elif token:tokens.append(token);token=''
        if token:tokens.append(token)
        assert tokens==[w['ciphertext'] for w in ledger if w['section']==section['id']]
        groups.append([sum(c in RUNES for c in t) for t in tokens])
    assert groups==fixed['section_lengths']
    assert data['section_ids']==[s['id'] for s in plan['sections']]
    orders=[list(p) for p in permutations(range(4))]
    assert data['orders']==orders
    reps=[order for order in orders if order[0]==0]
    mapping=[]
    for order in orders:
        zero=order.index(0)
        mapping.append(reps.index(order[zero:]+order[:zero]))
    assert data['class_representatives']==reps and data['order_class_indices']==mapping
    assert all(mapping.count(c)==4 for c in range(6))
    def all_scores(sections):
        profiles=[]
        for values in sections:
            profile=[0]*16
            for i,value in enumerate(values):profile[i%16]+=value
            profiles.append(profile)
        scores=[]
        for order in orders:
            sums=[0]*16;offset=0
            for section in order:
                for column,value in enumerate(profiles[section]):sums[(offset+column)%16]+=value
                offset+=len(sections[section])
            scores.append(256*sum(s*s for s in sums)-16*1796**2)
        return scores
    observed=all_scores(groups);minimum=min(observed)
    assert observed==data['observed_order_scores']
    assert [observed[orders.index(r)] for r in reps]==data['observed_class_scores']
    assert minimum==data['observed_minimum']
    assert [i for i,q in enumerate(observed) if q==minimum]==data['observed_minimizing_order_indices']
    rng=random.Random(330146);tail=0
    assert len(data['trials'])==data['trial_count']==49999 and data['seed']==330146
    for i,saved in enumerate(data['trials']):
        shuffled=[]
        for original in groups:
            positions=list(range(len(original)))
            for end in range(len(positions)-1,0,-1):
                pick=rng.randrange(end+1);positions[end],positions[pick]=positions[pick],positions[end]
            shuffled.append([original[p] for p in positions])
        scores=all_scores(shuffled)
        assert scores==[saved['class_scores'][c] for c in mapping]
        assert scores[0]==fixed['null_integer_scores'][i]
        low=min(scores)
        assert low==saved['minimum']
        assert [j for j,q in enumerate(scores) if q==low]==saved['minimizing_order_indices']
        tail+=low<=minimum
    p=Fraction(tail+1,50000)
    assert tail==data['lower_tail_with_ties']
    assert Fraction(data['p_fraction'])==p and data['p']==float(p)
    return {'report_sha256':sha(path),'checker_sha256':sha(Path(__file__)),
        'plan_sha256':sha(plan_path),'words_checked':464,'observed_orders_checked':24,
        'null_trials_checked':49999,'null_order_scores_checked':49999*24,
        'method':'Independent source scan, explicit index swaps and section-column accumulation; all 24 orders checked before each minimum. No producer import; Python random primitive shared.',
        'limits':'Selection adjustment covers the declared order search, not the original exploration.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    result=check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
