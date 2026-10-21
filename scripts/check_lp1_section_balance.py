"""Independent text scan, position-pair expectation and full permutation replay."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
ALPHABET=set('ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def check(path):
    data=json.loads(path.read_bytes());plan_path=ROOT/'experiments/plans/lp1-section-balance.json'
    assert sha(plan_path)==data['plan_sha256']=='d9d2a54271d6e64767e2091e360fc252c73a703cd7a0b6672090e615708e83b5'
    assert sha(ROOT/'scripts/lp1_section_balance.py')==data['producer_sha256']
    plan=json.loads(plan_path.read_bytes())
    for item in plan['inputs']:assert sha(ROOT/item['path'])==item['sha256']
    ledger=json.loads((ROOT/'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    groups=[]
    for section in plan['sections']:
        raw=''.join((ROOT/f'text/{page}.txt').read_text(encoding='utf-8') for page in section['pages'])
        raw=''.join(c for c in raw if c not in '/\r\n')
        tokens=[];token=''
        for i,c in enumerate(raw):
            if c in ALPHABET:token+=c
            elif c=="'" and token and i+1<len(raw) and raw[i+1] in ALPHABET:token+=c
            elif token:tokens.append(token);token=''
        if token:tokens.append(token)
        expected=[w for w in ledger if w['section']==section['id']]
        assert tokens==[w['ciphertext'] for w in expected]
        groups.append([sum(c in ALPHABET for c in t) for t in tokens])
    assert groups==data['section_lengths']
    assert [s['id'] for s in plan['sections']]==data['section_ids']
    assert list(map(len,groups))==plan['expected_words']
    values=[v for g in groups for v in g];k=16;m=29;total=sum(values)
    assert values==json.loads((ROOT/'experiments/records/lp1-word-length-balance/submitted-lengths.json').read_bytes())['lengths']
    def qscore(sequence):
        sums=[0]*k
        for position,value in enumerate(sequence):sums[position%k]+=value
        return k*k*sum(v*v for v in sums)-k*sum(sequence)**2
    observed=qscore(values)
    assert (data['words'],data['runes'],data['columns'],data['rows'])==(464,1796,k,m)
    assert data['observed_integer_score']==observed==128256
    memberships=[s for s,g in enumerate(groups) for _ in g]
    mu=[Fraction(sum(g),len(g)) for g in groups]
    second=[Fraction(sum(x*x for x in g),len(g)) for g in groups]
    pairs=[Fraction(sum(g)**2-sum(x*x for x in g),len(g)*(len(g)-1)) if len(g)>1 else None for g in groups]
    expected_squares=Fraction(0);means=[];variances=[]
    for column in range(k):
        slots=memberships[column::k]
        mean=sum(mu[s] for s in slots)
        square=sum(second[s] for s in slots)
        for i,a in enumerate(slots):
            for b in slots[i+1:]:square+=2*(pairs[a] if a==b else mu[a]*mu[b])
        means.append(mean);variances.append(square-mean*mean);expected_squares+=square
    counts=[[memberships[j::k].count(s) for j in range(k)] for s in range(4)]
    expectation=k*k*expected_squares-k*total*total
    assert data['section_column_slot_counts']==counts
    assert data['expected_column_sums']==list(map(str,means))
    assert data['column_sum_variances']==list(map(str,variances))
    scale=k**3*m*m
    assert Fraction(data['expected_integer_score'])==expectation
    assert Fraction(data['variance_of_column_means'])==Fraction(observed,scale)
    assert Fraction(data['expected_variance'])==expectation/scale
    assert Fraction(data['R_fraction'])==observed/expectation
    assert data['R']==float(observed/expectation)
    rng=random.Random(330146);scores=[]
    for trial in range(49999):
        sample=[]
        for original in groups:
            positions=list(range(len(original)))
            for i in range(len(positions)-1,0,-1):
                j=rng.randrange(i+1);positions[i],positions[j]=positions[j],positions[i]
            sample.extend(original[i] for i in positions)
        scores.append(qscore(sample))
    assert data['null_integer_scores']==scores
    tail=sum(v<=observed for v in scores)
    p=Fraction(tail+1,50000)
    assert (data['trials'],data['seed'],data['lower_tail_with_ties'])==(49999,330146,tail)
    assert Fraction(data['p_fraction'])==p and data['p']==float(p)
    return {'report_sha256':sha(path),'checker_sha256':sha(Path(__file__)),
        'plan_sha256':sha(plan_path),'words_checked':464,'null_scores_replayed':49999,
        'expectation_method':'Exact position-pair second moments; independent of section sample-sum formula.',
        'permutation_method':'Explicit Fisher-Yates index swaps and direct column accumulation; shared Python random primitive.',
        'limits':'Computational replay does not remove prior selection or validate a coherent-prose model.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',type=Path,required=True);args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    result=check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))
