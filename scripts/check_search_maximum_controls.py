"""Reconstruct every bounded-search candidate and maximum without producer imports."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/search-maximum-controls.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def check(path):
    report=json.loads(path.read_bytes());plan=json.loads(PLAN.read_bytes())
    assert report['plan_sha256']==sha(PLAN)
    assert report['producer_sha256']==sha(ROOT/'scripts/run_search_maximum_controls.py')
    for v in plan['inputs']:assert sha(ROOT/v['path'])==v['sha256'],v['path']
    counts=dict((g,int(n)) for g,n in (line.split() for line in (ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt').read_text(encoding='ascii').splitlines()))
    total=sum(counts.values())
    logprob={g:math.log10(n/total) for g,n in counts.items()};floor=math.log10(.01/total)
    def keys(seed):
        prefix=('liberpedia-decoder-control:'+str(seed)).encode('ascii')
        raw=b''.join(hashlib.sha256(prefix+counter.to_bytes(4,'big')).digest() for counter in range((plan['prefix_runes']+31)//32))
        return [v%29 for v in raw[:plan['prefix_runes']]]
    dictionary={s:keys(s) for s in plan['dictionary_seeds']}
    def compare(saved,expected):
        assert saved.keys()==expected.keys()
        for k,v in expected.items():
            if k=='score':assert math.isclose(saved[k],v,rel_tol=0,abs_tol=1e-12)
            else:assert saved[k]==v,k
    def scored(cipher,seed,key,truth):
        plain=bytes((v-key[i])%29 for i,v in enumerate(cipher))
        text=''.join(plan['latin'][i] for i in plain)
        grams=Counter(text[i:i+4] for i in range(len(text)-3))
        value=math.fsum(n*logprob.get(g,floor) for g,n in grams.items())/(len(text)-3)
        return {'seed':seed,'score':value,'candidate_sha256':hashlib.sha256(plain).hexdigest(),'matches_reference':plain==bytes(truth)}
    expected_pairs=[(i,s,r) for i,s in enumerate(plan['sections']) for r in range(plan['replicates'])]
    assert len(report['paired_searches'])==len(expected_pairs)==288
    checked=0
    for record,(index,section,replicate) in zip(report['paired_searches'],expected_pairs,strict=True):
        assert (record['section_index'],record['section'],record['replicate'])==(index,section,replicate)
        with (ROOT/f'exports/readings/{section}.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
        truth=[int(r['output_index']) for r in rows[:plan['prefix_runes']]]
        assert record['source_rows_available']==len(rows) and record['length']==len(truth)
        assert record['reference_sha256']==hashlib.sha256(bytes(truth)).hexdigest()
        null_seed=33010000+1000*index+replicate;true_seed=100000+replicate
        assert record['null_seed']==null_seed and record['true_seed']==true_seed
        rng=random.Random(null_seed);null=[rng.randrange(29) for _ in truth]
        true_key=keys(true_seed);positive=[(p+true_key[i])%29 for i,p in enumerate(truth)]
        true_candidate=scored(positive,true_seed,true_key,truth)
        assert true_candidate['matches_reference'];compare(record['true_candidate'],true_candidate)
        for kind,cipher in [('null',null),('positive',positive)]:
            saved=record[kind];assert saved['ciphertext']==cipher
            assert len(saved['candidates'])==len(plan['dictionary_seeds'])==256
            candidates=[]
            for value,seed in zip(saved['candidates'],plan['dictionary_seeds'],strict=True):
                expected=scored(cipher,seed,dictionary[seed],truth);compare(value,expected);candidates.append(expected);checked+=1
            assert len(saved['searches'])==len(plan['budgets'])
            previous=-math.inf
            for result,budget in zip(saved['searches'],plan['budgets'],strict=True):
                assert result['budget']==budget
                best=sorted(candidates[:budget],key=lambda c:(-c['score'],c['seed']))[0]
                compare(result['winner'],best)
                assert best['score']>=previous;previous=best['score']
                assert result['score_accepted']==(best['score']>=plan['threshold'])
                if kind=='positive':
                    included=sorted(candidates[:budget]+[true_candidate],key=lambda c:(-c['score'],c['seed']))[0]
                    assert result['included_candidate_count']==budget+1
                    compare(result['included_winner'],included)
                    assert result['included_score_accepted']==(included['score']>=plan['threshold'])
        if replicate==plan['replicates']-1:print('Independently checked',section,flush=True)
    assert checked==147456
    return {'status':'independent candidate and maximum replay passed; human review pending',
            'paired_searches_checked':288,'wrong_key_scores_checked':checked,'true_key_controls_checked':288,
            'report_sha256':sha(path),'checker_sha256':sha(Path(__file__))}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path);parser.add_argument('--receipt',required=True,type=Path);args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    receipt=check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))
