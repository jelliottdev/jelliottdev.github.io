"""Run the frozen nested wrong-key search and positive-key inclusion controls."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/plans/search-maximum-controls.json'


def key(seed,length):
    prefix=f'liberpedia-decoder-control:{seed}'.encode('ascii');values=[];counter=0
    while len(values)<length:
        values.extend(b%29 for b in hashlib.sha256(prefix+counter.to_bytes(4,'big')).digest());counter+=1
    return values[:length]


def winner(candidates):
    assert candidates
    return dict(min(candidates,key=lambda c:(-c['score'],c['seed'])))


def nested(candidates,budgets,threshold,true_candidate=None):
    rows=[];last=-math.inf
    for budget in budgets:
        selected=winner(candidates[:budget]);assert selected['score']>=last;last=selected['score']
        row={'budget':budget,'winner':selected,'score_accepted':selected['score']>=threshold}
        if true_candidate is not None:
            included=winner(candidates[:budget]+[true_candidate])
            row.update(included_candidate_count=budget+1,included_winner=included,
                       included_score_accepted=included['score']>=threshold)
        rows.append(row)
    return rows


def produce():
    plan=json.loads(PLAN.read_bytes())
    for item in plan['inputs']:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    counts={}
    for line in (ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,n=line.split();assert gram not in counts;counts[gram]=int(n)
    total=sum(counts.values());weights={g:math.log10(n)-math.log10(total) for g,n in counts.items()};floor=math.log10(.01)-math.log10(total)
    keys={s:key(s,plan['prefix_runes']) for s in plan['dictionary_seeds']}
    results=[]
    for section_index,section in enumerate(plan['sections']):
        with (ROOT/f'exports/readings/{section}.csv').open(encoding='utf-8',newline='') as source:all_rows=list(csv.DictReader(source))
        source_rows=all_rows[:plan['prefix_runes']];plain=[int(r['output_index']) for r in source_rows];n=len(plain)
        assert n>3
        def candidate(cipher,seed,k):
            p=[(c-k[i])%29 for i,c in enumerate(cipher)]
            text=''.join(plan['latin'][v] for v in p)
            score=sum(weights.get(text[i:i+4],floor) for i in range(len(text)-3))/(len(text)-3)
            return {'seed':seed,'score':score,'candidate_sha256':hashlib.sha256(bytes(p)).hexdigest(),'matches_reference':p==plain}
        for replicate in range(plan['replicates']):
            null_seed=33010000+1000*section_index+replicate;rng=random.Random(null_seed)
            null=[rng.randrange(29) for _ in range(n)]
            true_seed=100000+replicate;true_key=key(true_seed,n)
            positive=[(p+k)%29 for p,k in zip(plain,true_key,strict=True)]
            truth=candidate(positive,true_seed,true_key);assert truth['matches_reference']
            record={'section':section,'section_index':section_index,'replicate':replicate,'length':n,
                    'source_rows_available':len(all_rows),'reference_sha256':hashlib.sha256(bytes(plain)).hexdigest(),
                    'null_seed':null_seed,'true_seed':true_seed,'true_candidate':truth}
            for kind,cipher in [('null',null),('positive',positive)]:
                candidates=[candidate(cipher,s,keys[s]) for s in plan['dictionary_seeds']]
                record[kind]={'ciphertext':cipher,'candidates':candidates,
                              'searches':nested(candidates,plan['budgets'],plan['threshold'],truth if kind=='positive' else None)}
            results.append(record)
        print('Completed all search budgets for',section,flush=True)
    assert len(results)==288
    return {'status':'producer results; independent replay pending','plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            'producer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'paired_searches':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output path')
    result=produce()
    with args.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print('Saved 288 paired searches, 147456 wrong-key scores and 288 true-key controls')
