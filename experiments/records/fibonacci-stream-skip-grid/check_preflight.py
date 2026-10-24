"""Independent matrix alias recount and all planted cipher/score checks."""
import hashlib
import json
import math
import random
from collections import Counter

import engine as e


def model():
    counts={}
    for line in (e.LP/'data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        word,count=line.split()
        counts[word]=int(count)
    total=math.log10(sum(counts.values()))
    return {word:math.log10(count)-total for word,count in counts.items()}, math.log10(.01)-total


MODEL,FLOOR=model()


def score(text):
    return sum(MODEL.get(text[i:i+4],FLOOR) for i in range(len(text)-3))/(len(text)-3)


def main():
    aliases=json.loads((e.HERE/'aliases.json').read_text(encoding='utf8'))
    count=Counter()
    for r in aliases:
        a,b=r['a'],r['b']
        for _ in range(r['offset']):
            a,b=b,(a+b)%29
        expected=(r['sign']*a%29,r['sign']*b%29)
        assert expected==(r['canonical_a'],r['canonical_b'])
        count[expected]+=1
    assert len(aliases)==8410 and len(count)==841 and set(count.values())=={10}
    assert 4+4*(277-1)==1108 and 4+4*277+8==1120<1176
    result=json.loads((e.HERE/'control-results.json').read_text(encoding='utf8'))
    readings=json.loads((e.HERE/'known-readings.json').read_text(encoding='utf8'))
    keys=e.keys()
    for r in result['rows']:
        assert r['eligible']
        plain=readings[r['reading']]
        key=keys[r['a'],r['b']]
        rng=random.Random(r['seed'])
        pointer=0
        previous=None
        cipher=[]
        skips=[]
        used=[]
        for p in plain:
            skipped=0
            while True:
                c=(p-key[pointer])%29
                if previous is not None and c==previous and rng.random()<.83:
                    pointer+=1
                    skipped+=1
                else:
                    break
            cipher.append(c)
            skips.append(skipped)
            used.append(pointer)
            previous=c
            pointer+=1
        assert (cipher,skips,used)==(r['cipher'],r['skips'],r['used_key_positions'])
        assert r['full_exact']==(r['returned_indices']==plain)
        assert hashlib.sha256(bytes(r['returned_indices'])).hexdigest()==r['returned_sha256']
        assert abs(score(e.text(r['returned_indices']))-r['full_score'])<1e-10
        assert r['screen_pass']==(r['screen_score']>-6.5)
        assert r['full_pass']==(r['full_score']>-5.5)
    assert len(result['rows'])==841
    assert result['exact_complete_recovery']==sum(r['full_exact'] for r in result['rows'])
    assert result['zero_skip_plants']==sum(r['skip_total']==0 for r in result['rows'])
    receipt={'schema':'fibonacci-preflight-independent-check-v1','matrix_alias_mappings_recounted':8410,
             'canonical_pairs':841,'preimages_each':10,'independently_reconstructed_plants':841,
             'all_returned_control_paths_independently_rescored':841,
             'exact_complete_recovery':result['exact_complete_recovery'],
             'score_gate_passes':result['both_gates_pass'],'zero_skip_plants':result['zero_skip_plants'],
             'controls_sha256':e.sha(e.HERE/'control-results.json'),
             'limits':'Independent score and plant checks; not another native full-control campaign or a full-search error calibration.'}
    e.write(e.HERE/'preflight-independent-check.json',receipt)
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    main()
