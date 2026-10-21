"""Independent reconstruction of every stream, survivor and withheld result."""
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def regenerate(name,seed,n):
    constructor={'sha256':hashlib.sha256,'sha512':hashlib.sha512}[name]
    def symbols():
        for counter in itertools.count():
            block=constructor(b'liberpedia-seed-control:v1:'+struct.pack('>II',seed,counter)).digest()
            for byte in block:
                quotient,remainder=divmod(byte,29)
                if quotient<8:yield remainder
    return list(itertools.islice(symbols(),n))

def check(path):
    data=json.loads(path.read_bytes())
    plan_path=ROOT/'experiments/plans/seed-crib-controls.json'
    assert digest(plan_path)==data['plan_sha256']=='3c05cc4dff65835879f513d629cd0f0b43ece0d48fb1b1d31bddbdf2bdced456'
    plan=json.loads(plan_path.read_bytes())
    for source in plan['inputs']:assert digest(ROOT/source['path'])==source['sha256']
    assert digest(ROOT/'scripts/seed_crib_controls.py')==data['producer_sha256']
    with (ROOT/'exports/readings/lp2-57.csv').open(encoding='utf-8',newline='') as handle:
        plain=[int(row['output_index']) for row in csv.DictReader(handle)]
    assert len(plain)==95 and data['plaintext']==plain
    dictionaries={name:[regenerate(name,seed,95) for seed in range(4096)] for name in ['sha256','sha512']}
    assert data['dictionaries']==dictionaries
    expected_fixtures=[];expected_cells=[]
    for name in ['sha256','sha512']:
        for seed in [17,4095,4096]:
            key=regenerate(name,seed,95)
            ciphertext=[(plain[i]+key[i])%29 for i in range(95)]
            identifier=f'{name}:{seed}'
            expected_fixtures.append({'id':identifier,'generator':name,'seed':seed,'key':key,'ciphertext':ciphertext})
            for search in ['sha256','sha512']:
                for condition in ['correct','first-index-plus-one']:
                    for n in [2,4,8,16,32]:
                        survivors=[]
                        for candidate_seed,values in enumerate(dictionaries[search]):
                            # Check encryption of the assumed crib instead of subtracting a target stream.
                            matched=True
                            for position in range(n):
                                assumed=(plain[position]+(condition!='correct' and position==0))%29
                                if (assumed+values[position])%29!=ciphertext[position]:
                                    matched=False;break
                            if not matched:continue
                            decoded=[(ciphertext[i]+29-values[i])%29 for i in range(95)]
                            correct=[i for i in range(n,95) if decoded[i]==plain[i]]
                            survivors.append({'seed':candidate_seed,'decoded':decoded,
                                'whole_exact':all(decoded[i]==plain[i] for i in range(95)),
                                'suffix_exact':len(correct)==95-n,'suffix_correct_indices':len(correct)})
                        expected_cells.append({'fixture':identifier,'search_generator':search,'crib_condition':condition,
                            'crib_length':n,'generating_pair_in_search':name==search and seed in range(4096),
                            'survivors':survivors})
    assert data['fixtures']==expected_fixtures
    assert data['cells']==expected_cells
    return {'report_sha256':digest(path),'checker_sha256':digest(Path(__file__)),
        'plan_sha256':digest(plan_path),'candidate_streams_checked':8192,'fixtures_checked':6,'cells_checked':120,
        'method':'Separate struct-packed inputs, hash constructors, divmod rejection, direct crib encryption and full survivor reconstruction; no producer imports. Shares Python hashlib primitives.',
        'limits':'Checks the declared synthetic experiment, not the assumptions of an unknown manuscript cipher.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('--receipt',type=Path,required=True)
    args=parser.parse_args()
    if args.receipt.exists():parser.error('Choose a new receipt path')
    result=check(args.report)
    with args.receipt.open('x',encoding='utf-8',newline='\n') as handle:
        json.dump(result,handle,indent=2);handle.write('\n')
    print(json.dumps(result,indent=2))
