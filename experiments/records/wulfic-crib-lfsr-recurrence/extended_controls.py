"""Pre-outcome endpoint plants for the declared order-4/5 screen."""
import argparse
import json
import random
from pathlib import Path

import run
import check

H = Path(__file__).resolve().parent
plan = json.loads((H / 'plan.json').read_text(encoding='utf-8'))
crib = plan['cribs']['CIRCUMFERENCE']
rows = []
for mode in plan['modes']:
    for order in (4,5):
        for offset in (7,23):
            length = offset + len(crib) + 128 + 5
            rng = random.Random(4400 + 100*order + offset)
            plain = [rng.randrange(29) for _ in range(length)]
            plain[offset:offset+len(crib)] = crib
            key = [3,7,11,13,17][:order]
            coefficients = [2,3,5,7,11][:order]
            while len(key) < length:
                key.append(sum(a*b for a,b in zip(coefficients,key[-order:]))%29)
            if mode == 'sub':
                cipher = [(p+k)%29 for p,k in zip(plain,key)]
            elif mode == 'add':
                cipher = [(p-k)%29 for p,k in zip(plain,key)]
            else:
                cipher = [(k-p)%29 for p,k in zip(plain,key)]
            found = run.infer(cipher,crib,offset,mode)
            observed = run.decrypt(cipher[offset+len(crib):offset+len(crib)+128],
                                   found[0],mode) if found else []
            target = plain[offset+len(crib):offset+len(crib)+128]
            inferred_key = check.key_for(cipher[offset:offset+len(crib)],crib,mode)
            poly,degree = check.connection(inferred_key[:-2])
            independently_valid = degree == order and check.extend(inferred_key[:-2],poly,len(crib)+128) == key[offset:offset+len(crib)+128]
            rows.append({'mode':mode,'order':order,'offset':offset,
                         'actual_inferred_order':found[1] if found else None,
                         'full_128_recovered':observed == target,
                         'independent_recurrence':independently_valid})
assert all(r['full_128_recovered'] and r['independent_recurrence'] for r in rows), rows
receipt = {'schema':'wulfic-lfsr-endpoint-controls-v1',
           'timing':'Run before manuscript target outcomes were returned',
           'rows':rows}
parser = argparse.ArgumentParser()
parser.add_argument('--check',action='store_true')
if parser.parse_args().check:
    assert receipt == json.loads((H/'extended-controls.json').read_text(encoding='utf-8'))
else:
    (H/'extended-controls.json').write_text(json.dumps(receipt,indent=2)+'\n',
                                           encoding='utf-8',newline='\n')
print(len(rows),'order-4/5 plants pass')
