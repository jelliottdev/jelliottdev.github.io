"""Recompute the pinned source-menu32 control screen; no manuscript targets."""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIGITS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

def fitness(values, target):
    count = len(values)
    distribution = [values.count(i) / count for i in range(29)]
    js = 0.0
    for p, q in zip(distribution, target):
        m = (p + q) / 2
        if p: js += .5 * p * math.log(p / m)
        if q: js += .5 * q * math.log(q / m)
    return 1 / (1 + js)

def key_streams(fixture):
    base60 = []
    for pair in fixture['source_secret_grid_pairs']:
        value = 0
        for char in pair:
            value = 60 * value + DIGITS.index(char)
        base60.append(value % 29)
    return [('Source 256-pair stream', base60), ('2013 missing-prime stream', [p % 29 for p in fixture['missing_primes']])]

def route_positions(n, width, route):
    rows=(n+width-1)//width
    grid=[[r*width+c if r*width+c<n else None for c in range(width)] for r in range(rows)]
    positions=[]
    if route=='column':
        for c in range(width):
            for r in range(rows):
                if grid[r][c] is not None: positions.append(grid[r][c])
    elif route=='diagonal':
        for k in range(rows+width-1):
            for j in range(k+1):
                r,c=j,k-j
                if r<rows and c<width and grid[r][c] is not None: positions.append(grid[r][c])
    else:
        top,bottom,left,right=0,rows-1,0,width-1
        while top<=bottom and left<=right:
            for c in range(left,right+1):
                if grid[top][c] is not None: positions.append(grid[top][c])
            top+=1
            for r in range(top,bottom+1):
                if grid[r][right] is not None: positions.append(grid[r][right])
            right-=1
            if top<=bottom:
                for c in range(right,left-1,-1):
                    if grid[bottom][c] is not None: positions.append(grid[bottom][c])
                bottom-=1
            if left<=right:
                for r in range(bottom,top-1,-1):
                    if grid[r][left] is not None: positions.append(grid[r][left])
                left+=1
    assert len(positions)==n and sorted(positions)==list(range(n))
    return positions

def run():
    fixture = json.loads((HERE / 'fixture.json').read_text(encoding='utf-8'))
    prior = json.loads((HERE / 'plan-frozen.json').read_text(encoding='utf-8'))
    amendment = json.loads((HERE / 'calibration-amendment.json').read_text(encoding='utf-8'))
    assert amendment['original_plan_sha256'] == hashlib.sha256((HERE / 'plan-frozen.json').read_bytes()).hexdigest()
    assert prior['source']['revision'] == fixture['source_revision']
    primes = fixture['gp_rune_primes']
    missing = fixture['missing_primes']
    assert len(primes) == 29 and len(missing) == 180 and len(fixture['source_secret_grid_pairs']) == 256
    assert missing == [n for n in range(73, 1224) if all(n % k for k in range(2, math.isqrt(n) + 1))]
    gaps = [{'cell_zero_based':i,'source_secret':left,'source_page':right} for i, (left,right) in enumerate(zip(fixture['source_secret_grid_pairs'], fixture['source_pages_grid_pairs'])) if left != right]
    assert len(gaps) == 5
    assert fixture['source_secret_grid_pairs'] == fixture['site_transcription_grid_pairs']
    hitset = set(missing)
    def launches(words):
        runlength = 0
        positions = []
        for wi, word in enumerate(words):
            s = sum(primes[i] for i in word)
            hit = (s in hitset and (len(word) > 1 or s > 120)) or 3301-s in hitset
            runlength = runlength+1 if hit else 0
            if runlength >= 3: positions.append(wi-2)
        return positions
    positive_words = [[0,19],[1,2,19],[3,2,19]]
    negative_words = [[0,19],[1,2,19],[0],[3,2,19]]
    assert launches(positive_words) == [0] and launches(negative_words) == []
    known = fixture['known_direct_source_page5_indices']
    target = fixture['source_known_reading_unigram_target']
    assert len(known) == 157 and len(target) == 29
    known_fitness = fitness(known,target)
    assert known_fitness > .91
    keys = []
    for name,key in key_streams(fixture):
        cipher = [(28 + 3 - value + key[i % len(key)]) % 29 for i,value in enumerate(known)]
        recovered = [(28 - ((c-key[i % len(key)]) % 29) + 3) % 29 for i,c in enumerate(cipher)]
        assert recovered == known
        maxima = []
        for rep in range(199):
            shuffled = cipher.copy()
            random.Random(3301+rep).shuffle(shuffled)
            base = [(c-key[i % len(key)]) % 29 for i,c in enumerate(shuffled)]
            maxima.append(max(fitness([(28-x+s) % 29 for x in base],target) for s in range(29)))
        keys.append({'name':name,'length':len(key),'planted_recovered':True,'planted_fitness':known_fitness,'null_maxima':maxima,'null_pass_count':sum(x > .91 for x in maxima)})
    route_maxima=[]
    route_plants=[]
    for width in (3,7):
        for route in ('column','diagonal','spiral'):
            order=route_positions(len(known),width,route)
            ciphertext=[None]*len(known)
            for j,pos in enumerate(order):
                ciphertext[pos]=(28+3-known[j])%29
            decoded=[(28-ciphertext[pos]+3)%29 for pos in order]
            assert decoded==known
            route_plants.append({'route':route,'width':width,'position_sha256':hashlib.sha256(','.join(map(str,order)).encode()).hexdigest(),'recovered_exactly':True,'fitness':fitness(decoded,target)})
    route_cipher=[(28+3-value)%29 for value in known]
    for rep in range(199):
        shuffled=route_cipher.copy()
        random.Random(3301+rep).shuffle(shuffled)
        route_maxima.append(max(fitness([(28-x+s)%29 for x in shuffled],target) for s in range(29)))
    assert max(route_maxima)-min(route_maxima) < 1e-14
    return {'schema':'liberpedia-d4v1-menu32-source-gate-result-v1','plan_sha256':hashlib.sha256((HERE/'plan-frozen.json').read_bytes()).hexdigest(),'calibration_amendment_sha256':hashlib.sha256((HERE/'calibration-amendment.json').read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256((HERE/'fixture.json').read_bytes()).hexdigest(),'source_revision':fixture['source_revision'],'target_manuscript_decodes':0,'missing_prime_count':len(missing),'source_grid_pair_count':256,'source_secret_vs_source_page_cells':gaps,'site_pair_list_matches_source_secret':True,'punctuation_crosswalk':fixture['source_site_punctuation_crosswalk'],'trigger_positive_starts':launches(positive_words),'trigger_negative_starts':launches(negative_words),'known_direct_page5_rune_count':len(known),'known_direct_page5_fitness':known_fitness,'key_controls':keys,'route_control':{'inversion_plants':6,'plants_recovered':6,'route_plants':route_plants,'route_invariance':'Unigram fitness is identical under every permutation for fixed Atbash shift.','null_replicates':199,'null_maxima':route_maxima,'null_pass_count':sum(x > .90 for x in route_maxima)}}

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=run()
    content=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    target=HERE/'results.json'
    if args.check:
        assert target.read_text(encoding='utf-8') == content
        print('PASS: complete source controls and all 199 null maxima match')
    else:
        target.write_text(content,encoding='utf-8',newline='\n')
