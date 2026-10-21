"""Exact known-prefix seed search; synthetic controls, not a manuscript attack."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT/'experiments/plans/seed-crib-controls.json'
DOMAIN = b'liberpedia-seed-control:v1:'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def accepted(data):
    return [b % 29 for b in data if b < 232]

def digest_input(seed, counter):
    return DOMAIN + seed.to_bytes(4, 'big') + counter.to_bytes(4, 'big')

def stream(generator, seed, length):
    values = []
    counter = 0
    while len(values) < length:
        values.extend(accepted(hashlib.new(generator, digest_input(seed, counter)).digest()))
        counter += 1
    return values[:length]

def produce():
    assert sha(PLAN) == '3c05cc4dff65835879f513d629cd0f0b43ece0d48fb1b1d31bddbdf2bdced456'
    plan = json.loads(PLAN.read_bytes())
    for source in plan['inputs']:
        assert sha(ROOT/source['path']) == source['sha256'], source['path']
    with (ROOT/'exports/readings/lp2-57.csv').open(encoding='utf-8',newline='') as handle:
        plain = [int(row['output_index']) for row in csv.DictReader(handle)]
    assert len(plain) == plan['length'] == 95
    assert all(0 <= p < 29 for p in plain)
    dictionaries = {g:[stream(g,s,len(plain)) for s in range(4096)] for g in plan['generators']}
    fixtures = []
    cells = []
    for generator in plan['generators']:
        for seed in plan['planted_seeds']:
            key = stream(generator,seed,len(plain))
            cipher = [(p+k)%29 for p,k in zip(plain,key)]
            identifier = f'{generator}:{seed}'
            fixtures.append({'id':identifier,'generator':generator,'seed':seed,'key':key,'ciphertext':cipher})
            for search_generator, candidates in dictionaries.items():
                for condition in plan['crib_conditions']:
                    assumed = plain.copy()
                    if condition == 'first-index-plus-one': assumed[0] = (assumed[0]+1)%29
                    for length in plan['crib_lengths']:
                        needed = [(c-p)%29 for c,p in zip(cipher[:length],assumed[:length])]
                        survivors = []
                        for candidate_seed,candidate_key in enumerate(candidates):
                            if candidate_key[:length] != needed: continue
                            decoded = [(c-k)%29 for c,k in zip(cipher,candidate_key)]
                            survivors.append({'seed':candidate_seed,'decoded':decoded,
                                'whole_exact':decoded==plain,'suffix_exact':decoded[length:]==plain[length:],
                                'suffix_correct_indices':sum(a==b for a,b in zip(decoded[length:],plain[length:]))})
                        cells.append({'fixture':identifier,'search_generator':search_generator,'crib_condition':condition,
                            'crib_length':length,'generating_pair_in_search':generator==search_generator and seed<4096,
                            'survivors':survivors})
    assert len(cells)==plan['expected_cells']==120
    return {'plan_sha256':sha(PLAN),'producer_sha256':sha(Path(__file__)),
        'plaintext':plain,'dictionaries':dictionaries,'fixtures':fixtures,'cells':cells,
        'limits':'Synthetic exact-alignment known-plaintext controls; no manuscript identification or recovery probability.'}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():parser.error('Choose a new output path')
    result=produce()
    with args.output.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(result,handle,separators=(',',':'));handle.write('\n')
    print('Preserved 8192 candidate streams, six planted fixtures and 120 complete result cells.')
