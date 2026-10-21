"""Fixed section-preserving shuffle sensitivity test for the 464-word object."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/lp1-section-balance.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def score(values,k):
    total=sum(values)
    return sum((k*sum(values[j::k])-total)**2 for j in range(k))

def expected_score(groups,k):
    means=[Fraction(0) for _ in range(k)]
    variances=[Fraction(0) for _ in range(k)]
    offset=0;slot_counts=[]
    for values in groups:
        n=len(values);mu=Fraction(sum(values),n)
        variance=sum((x-mu)**2 for x in values)/n
        counts=[sum((offset+i)%k==j for i in range(n)) for j in range(k)]
        slot_counts.append(counts)
        for j,count in enumerate(counts):
            means[j]+=count*mu
            if n>1:variances[j]+=Fraction(count*(n-count),n-1)*variance
        offset+=n
    total=sum(map(sum,groups))
    expectation=sum(k*k*variances[j]+(k*means[j]-total)**2 for j in range(k))
    return expectation,slot_counts,means,variances

def produce():
    assert sha(PLAN)=='d9d2a54271d6e64767e2091e360fc252c73a703cd7a0b6672090e615708e83b5'
    plan=json.loads(PLAN.read_bytes())
    for item in plan['inputs']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    ledger=json.loads((ROOT/'experiments/records/lp1-word-length-balance/words.json').read_bytes())
    groups=[[w['rune_length'] for w in ledger if w['section']==s['id']] for s in plan['sections']]
    assert list(map(len,groups))==plan['expected_words']
    values=sum(groups,[])
    assert values==json.loads((ROOT/'experiments/records/lp1-word-length-balance/submitted-lengths.json').read_bytes())['lengths']
    assert len(values)==464 and sum(values)==1796
    k=plan['columns'];m=len(values)//k
    observed=score(values,k)
    expected,counts,means,variances=expected_score(groups,k)
    rng=random.Random(plan['seed']);null=[]
    for _ in range(plan['trials']):
        sample=[]
        for original in groups:
            section=original.copy();rng.shuffle(section);sample.extend(section)
        null.append(score(sample,k))
    tail=sum(q<=observed for q in null)
    p=Fraction(tail+1,len(null)+1)
    scale=k**3*m**2
    return {'plan_sha256':sha(PLAN),'producer_sha256':sha(Path(__file__)),
        'section_ids':[s['id'] for s in plan['sections']],'section_lengths':groups,
        'section_column_slot_counts':counts,'expected_column_sums':list(map(str,means)),
        'column_sum_variances':list(map(str,variances)),
        'words':len(values),'runes':sum(values),'columns':k,'rows':m,
        'observed_integer_score':observed,'expected_integer_score':str(expected),
        'variance_of_column_means':str(Fraction(observed,scale)),
        'expected_variance':str(expected/scale),'R_fraction':str(observed/expected),
        'R':float(observed/expected),'trials':len(null),'seed':plan['seed'],
        'lower_tail_with_ties':tail,'p_fraction':str(p),'p':float(p),'null_integer_scores':null,
        'limits':'Selected arrangement; dependent sensitivity comparison, not exploration-adjusted evidence or coherent-prose null.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output file')
    result=produce()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,separators=(',',':'));f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['null_integer_scores','section_lengths']},indent=2))
