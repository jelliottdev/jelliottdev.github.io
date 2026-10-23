"""Independent scalar reconstruction of source outputs and selection controls."""
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LABELS=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
        'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA')


def prime(n):
    if n<2:return False
    return all(n%d for d in range(2,math.isqrt(n)+1))


def scalar_columnar(values,width):
    return [values[position] for column in range(width)
            for position in range(column,len(values),width)]


def scalar_ioc(values):
    if len(values)<2:return 0.0
    counts=Counter(values)
    return 29*sum(count*(count-1) for count in counts.values())/(len(values)*(len(values)-1))


def scalar_score(values,weights):
    text=''.join(LABELS[value] for value in values)
    return sum(weights[tri] for tri in weights for i in range(len(text)-2) if text[i:i+3]==tri)


def all_candidates(page,weights):
    prime0=[page[position] for position in range(len(page)) if prime(position)]
    ranked=[]
    for width in range(2,15):
        transposed=scalar_columnar(prime0,width)
        for shift in range(29):
            plain=[(value-shift)%29 for value in transposed]
            ranked.append((scalar_score(plain,weights),scalar_ioc(plain),width,shift,plain))
    ranked.sort(key=lambda row:(-row[0],-row[1]))
    return ranked


def main():
    inputs=json.loads((HERE/'inputs.json').read_text(encoding='utf-8'))
    result=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'inputs.json').read_bytes()).hexdigest()==result['input_sha256']
    assert hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()==result['plan_sha256']
    assert hashlib.sha256((HERE/'positive.json').read_bytes()).hexdigest()==result['positive_sha256']
    assert hashlib.sha256((ROOT/inputs['site_path']).read_bytes()).hexdigest()==inputs['site_sha256']
    cipher=inputs['runes'];weights=inputs['trigram_weights']
    prime0=[cipher[i] for i in range(len(cipher)) if prime(i)]
    prime1=[cipher[i-1] for i in range(2,len(cipher)+1) if prime(i)]
    nonprime=[cipher[i] for i in range(len(cipher)) if not prime(i)]
    arms={'prime0':prime0,'prime1':prime1,'nonprime0':nonprime}
    for width in (5,7,11,13):arms[f'whole_columnar_{width}']=scalar_columnar(cipher,width)
    assert set(arms)==set(result['stage_one'])
    for name,stream in arms.items():
        saved=result['stage_one'][name]
        assert len(stream)==saved['selected_runes']
        assert hashlib.sha256(bytes(stream)).hexdigest()==saved['stream_sha256']
        assert ''.join(LABELS[value] for value in stream)==saved['runeglish']
        assert abs(scalar_ioc(stream)-saved['normalized_ioc'])<1e-12
    ranked=all_candidates(cipher,weights)
    assert len(ranked)==result['stage_two']['source_settings']==377
    assert all(abs(row[1]-result['stage_two']['constant_normalized_ioc'])<1e-12 for row in ranked)
    for row,saved in zip(ranked,result['stage_two']['ranked']):
        score,ioc,width,shift,plain=row
        assert (score,width,shift)==(saved['trigram_score'],saved['width'],saved['shift'])
        assert hashlib.sha256(bytes(plain)).hexdigest()==saved['output_sha256']
        if saved['runeglish'] is not None:
            assert ''.join(LABELS[value] for value in plain)==saved['runeglish']
    assert len(result['null'])==256
    for trial,saved in enumerate(result['null']):
        shuffled=cipher[:]
        random.Random(20261023+trial).shuffle(shuffled)
        best=all_candidates(shuffled,weights)[0]
        assert (saved['trial'],saved['max_trigram_score'],saved['width'],saved['shift']) == (
            trial,best[0],best[2],best[3])
    tail=sum(x['max_trigram_score']>=ranked[0][0] for x in result['null'])
    assert result['null_ge_observed']==tail
    assert result['add_one_tail_fraction']==f'{tail+1}/257'
    print('PASS: independent page arms, all 377 ranked outputs, invariant IoC and 256 full-search controls')


if __name__=='__main__':main()
