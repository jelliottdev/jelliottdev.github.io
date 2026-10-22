"""Independent full-offset replay with a counted-quadgram scorer."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
saved=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
assert hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest()==saved['plan_sha256']
for entry in plan['inputs']:
    assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256']

alphabet=json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
labels=[row['latin'] for row in alphabet]
index={row['rune']:i for i,row in enumerate(alphabet)}
paragraphs=json.loads((ROOT/'exports/sources/emerson-paragraphs.json').read_text(encoding='utf-8'))
source=''.join(char for char in ' '.join(row['text'] for row in paragraphs).upper() if char.isascii() and char.isalpha())
assert len(source)==saved['source']['normalized_letters']==43516
assert hashlib.sha256(source.encode('ascii')).hexdigest()==saved['source']['normalized_sha256']
original=[ord(char)-65 for char in source]
counts=dict(line.split() for line in (ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt').read_text(encoding='ascii').splitlines())
total=sum(map(int,counts.values()))
logp={gram:math.log10(int(amount)/total) for gram,amount in counts.items()}
floor=math.log10(0.01/total)

def evaluate(indices,key,offset,start,length):
    text=''.join(labels[(indices[start+i]-key[offset+start+i])%29] for i in range(length))
    groups=Counter(text[i:i+4] for i in range(len(text)-3))
    score=sum(count*logp.get(gram,floor) for gram,count in groups.items())/(len(text)-3)
    return text,score

def replay(cipher,key,stored):
    n=plan['selection_runes'];m=plan['holdout_runes']
    limit=len(key)-n-m+1
    assert stored['offsets_searched']==limit
    best=[]
    for offset in range(limit):
        _,value=evaluate(cipher,key,offset,0,n)
        best.append((value,-offset))
    best=sorted(best,reverse=True)[:5]
    assert [-offset for _,offset in best]==[row['offset_zero_based'] for row in stored['top_five']]
    for (_,minus_offset),row in zip(best,stored['top_five']):
        offset=-minus_offset
        first,first_score=evaluate(cipher,key,offset,0,n)
        later,later_score=evaluate(cipher,key,offset,n,m)
        assert first==row['selection_latin'] and later==row['continuation_latin']
        assert math.isclose(first_score,row['selection_score'],rel_tol=0,abs_tol=1e-12)
        assert math.isclose(later_score,row['continuation_score'],rel_tol=0,abs_tol=1e-12)
        assert hashlib.sha256(first.encode('ascii')).hexdigest()==row['selection_sha256']
        assert hashlib.sha256(later.encode('ascii')).hexdigest()==row['continuation_sha256']

for target in saved['targets']:
    raw=(ROOT/f'text/{target["page"]}.txt').read_text(encoding='utf-8')
    cipher=[index[char] for char in raw if char in index]
    assert len(cipher)==target['page_runes']
    for row in target['searches']:
        if row['source']=='archived-emerson':key=original
        else:
            seed=int(row['source'].removeprefix('letter-shuffle-'))
            assert 330100<=seed<=330107
            key=original.copy();random.Random(seed).shuffle(key)
        assert hashlib.sha256(bytes(key)).hexdigest()==row['source_sha256']
        replay(cipher,key,row)
known=json.loads((ROOT/'data/evidence/known-readings.json').read_text(encoding='utf-8'))
plain=next(c for c in known['controls'] if c['id']=='first-koan')['decoded_pages'][0]['rune_indices'][:192]
cipher=[(p+original[3301+i])%29 for i,p in enumerate(plain)]
replay(cipher,original,saved['planted_control'])
assert saved['planted_control']['true_offset_selected_first']
assert saved['planted_control']['top_five'][0]['offset_zero_based']==3301
assert [(c-original[3301+i])%29 for i,c in enumerate(cipher)]==plain
print('PASS: independent counted-gram replay verifies every full-offset maximum, top five, holdout and planted recovery')
