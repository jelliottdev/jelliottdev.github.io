"""Independent scalar check of the complete menu32 pretarget control ledger."""
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
f=json.loads((HERE/'fixture.json').read_text(encoding='utf-8'))
r=json.loads((HERE/'results.json').read_text(encoding='utf-8'))
assert r['target_manuscript_decodes']==0
for name in ('plan-frozen.json','calibration-amendment.json','fixture.json'):
    key={'plan-frozen.json':'plan_sha256','calibration-amendment.json':'calibration_amendment_sha256','fixture.json':'fixture_sha256'}[name]
    assert r[key]==hashlib.sha256((HERE/name).read_bytes()).hexdigest()
assert len(f['gp_rune_primes'])==29 and len(f['missing_primes'])==180
assert all(i in range(29) for i in f['known_direct_source_page5_indices'])
assert len(f['source_secret_grid_pairs'])==len(f['source_pages_grid_pairs'])==len(f['site_transcription_grid_pairs'])==256
assert f['source_secret_grid_pairs']==f['site_transcription_grid_pairs']
errors=[(i,a,b) for i,(a,b) in enumerate(zip(f['source_secret_grid_pairs'],f['source_pages_grid_pairs'])) if a!=b]
assert errors==[(x['cell_zero_based'],x['source_secret'],x['source_page']) for x in r['source_secret_vs_source_page_cells']]
assert [i for i,_,_ in errors]==[45,50,165,172,246]

prime=set(f['missing_primes'])
assert prime=={n for n in range(73,1224) if n>1 and all(n%k for k in range(2,math.isqrt(n)+1))}
values=f['gp_rune_primes']
def word_flag(word):
    total=math.fsum(values[x] for x in word)
    return bool((total in prime and (len(word)>1 or total>120)) or 3301-total in prime)
def anchor_count(words):
    runs=0; count=0
    for word in words:
        runs=(runs+1) if word_flag(word) else 0
        if runs>=3:count+=1
    return count
assert anchor_count([[0,19],[1,2,19],[3,2,19]])==1
assert anchor_count([[0,19],[1,2,19],[0],[3,2,19]])==0
assert r['trigger_positive_starts']==[0] and r['trigger_negative_starts']==[]

alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
def score(seq):
    counts=Counter(seq);n=len(seq)
    q=f['source_known_reading_unigram_target']
    terms=[]
    for i in range(29):
        p=counts[i]/n; m=(p+q[i])/2
        if p:terms.append(p*math.log(p/m)/2)
        if q[i]:terms.append(q[i]*math.log(q[i]/m)/2)
    return 1/(1+math.fsum(terms))
known=f['known_direct_source_page5_indices']
assert len(known)==157
assert abs(score(known)-r['known_direct_page5_fitness'])<1e-13
for row in r['key_controls']:
    if row['name']=='Source 256-pair stream':
        key=[(alphabet.index(x[0])*60+alphabet.index(x[1]))%29 for x in f['source_secret_grid_pairs']]
    else:
        key=[x%29 for x in f['missing_primes']]
    assert len(key)==row['length']
    cipher=[(28+3-p+key[i%len(key)])%29 for i,p in enumerate(known)]
    assert [(28-(cipher[i]-key[i%len(key)])+3)%29 for i in range(len(known))]==known
    for rep,expected in enumerate(row['null_maxima']):
        rng=random.Random(3301+rep)
        order=list(range(len(cipher)))
        rng.shuffle(order)
        shuffled=[cipher[i] for i in order]
        base=[(x-key[i%len(key)])%29 for i,x in enumerate(shuffled)]
        best=max(score([(28-x+shift)%29 for x in base]) for shift in range(29))
        assert abs(best-expected)<1e-12,(row['name'],rep,best,expected)
    assert row['null_pass_count']==sum(x>.91 for x in row['null_maxima'])==199
assert len(r['route_control']['null_maxima'])==199
assert r['route_control']['null_pass_count']==199
assert max(r['route_control']['null_maxima'])-min(r['route_control']['null_maxima'])<1e-13
route_cipher=[(28+3-value)%29 for value in known]
route_best=max(score([(28-value+shift)%29 for value in route_cipher]) for shift in range(29))
assert all(abs(value-route_best)<1e-13 for value in r['route_control']['null_maxima'])
assert len(r['route_control']['route_plants'])==6
for item in r['route_control']['route_plants']:
    width=item['width']; height=(len(known)+width-1)//width
    cells={(row,col):row*width+col for row in range(height) for col in range(width) if row*width+col<len(known)}
    if item['route']=='column':
        coords=sorted(cells,key=lambda z:(z[1],z[0]))
    elif item['route']=='diagonal':
        coords=sorted(cells,key=lambda z:(z[0]+z[1],z[0]))
    else:
        coords=[]
        top,bottom,left,right=0,height-1,0,width-1
        while top<=bottom and left<=right:
            coords.extend((top,c) for c in range(left,right+1))
            top+=1
            coords.extend((row,right) for row in range(top,bottom+1))
            right-=1
            if top<=bottom:
                coords.extend((bottom,c) for c in range(right,left-1,-1))
                bottom-=1
            if left<=right:
                coords.extend((row,left) for row in range(bottom,top-1,-1))
                left+=1
        coords=[z for z in coords if z in cells]
    positions=[cells[z] for z in coords]
    assert len(positions)==len(known) and len(set(positions))==len(known)
    assert hashlib.sha256(','.join(map(str,positions)).encode()).hexdigest()==item['position_sha256']
    ciphertext=[None]*len(known)
    for position,plaintext in zip(positions,known):
        ciphertext[position]=(28+3-plaintext)%29
    assert [(28-ciphertext[position]+3)%29 for position in positions]==known
    assert abs(score(known)-item['fitness'])<1e-13 and item['recovered_exactly']
# A permutation preserves Counter(seq), hence score(seq) for this unigram model.
for width in (3,7):
    for move in (1,3,7):
        permutation=list(range(len(known)))
        permutation=permutation[move::width]+permutation[:move:width]+[x for x in permutation if x not in set(permutation[move::width]+permutation[:move:width])]
        assert sorted(permutation)==list(range(len(known)))
        assert abs(score(known)-score([known[i] for i in permutation]))<1e-14
print('PASS: 2 source keys, 398 shuffled-key maxima, 6 source-route plants, route-invariant unigram check, and source gate fixtures')
