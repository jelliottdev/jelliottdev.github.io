"""Bounded full-offset additive running-key search using pinned Emerson text."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def model():
    counts = {}
    for line in (ROOT/'experiments/records/english-scorer-controls/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram, amount = line.split()
        counts[gram] = int(amount)
    total = sum(counts.values())
    normalizer = math.log10(total)
    return ({gram: math.log10(amount)-normalizer for gram, amount in counts.items()},
            math.log10(0.01)-normalizer, total)


def score(text, probabilities, floor):
    return sum(probabilities.get(text[i:i+4], floor) for i in range(len(text)-3))/(len(text)-3)


def search(cipher, key, labels, probabilities, floor, selection, holdout):
    full = selection + holdout
    candidates = len(key)-full+1
    assert candidates > 0 and len(cipher) >= full
    top = []
    for offset in range(candidates):
        opening = ''.join(labels[(cipher[i]-key[offset+i])%29] for i in range(selection))
        value = score(opening, probabilities, floor)
        entry = (value, -offset)
        if len(top) < 5 or entry > top[-1][0]:
            top.append((entry, offset, opening))
            top.sort(key=lambda item: item[0], reverse=True)
            if len(top) > 5:
                top.pop()
    rows = []
    for (_, offset, opening) in top:
        continuation = ''.join(labels[(cipher[selection+i]-key[offset+selection+i])%29] for i in range(holdout))
        rows.append({'offset_zero_based': offset, 'selection_score': score(opening, probabilities, floor),
                     'continuation_score': score(continuation, probabilities, floor),
                     'selection_latin': opening, 'continuation_latin': continuation,
                     'selection_sha256': sha(opening.encode('ascii')),
                     'continuation_sha256': sha(continuation.encode('ascii'))})
    return {'offsets_searched': candidates, 'top_five': rows}


def report():
    plan_bytes = (HERE/'plan.json').read_bytes()
    plan = json.loads(plan_bytes)
    for row in plan['inputs']:
        assert sha((ROOT/row['path']).read_bytes()) == row['sha256'], row['path']
    alphabet = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']
    labels = [row['latin'] for row in alphabet]
    lookup = {row['rune']: i for i, row in enumerate(alphabet)}
    paragraphs = json.loads((ROOT/'exports/sources/emerson-paragraphs.json').read_text(encoding='utf-8'))
    assert len(paragraphs) == 50
    normalized = ''.join(c for c in ' '.join(p['text'] for p in paragraphs).upper() if 'A' <= c <= 'Z')
    key = [ord(c)-65 for c in normalized]
    assert len(key) == 43516
    selection = plan['selection_runes']; holdout = plan['holdout_runes']
    probabilities, floor, model_total = model()
    page_cipher = {}
    for page in plan['targets']:
        raw = (ROOT/f'text/{page}.txt').read_text(encoding='utf-8')
        stream = [lookup[c] for c in raw if c in lookup]
        assert len(stream) >= selection+holdout
        page_cipher[page] = stream
    known = json.loads((ROOT/'data/evidence/known-readings.json').read_text(encoding='utf-8'))
    lp1 = next(row for row in known['controls'] if row['id'] == 'first-koan')['decoded_pages'][0]['rune_indices'][:selection+holdout]
    assert len(lp1) == selection+holdout
    planted_offset = 3301
    plant_cipher = [(p+key[planted_offset+i])%29 for i,p in enumerate(lp1)]
    controls = [{'name':'archived-emerson','key':key}]
    for seed in range(330100,330108):
        shuffled = key.copy()
        random.Random(seed).shuffle(shuffled)
        controls.append({'name':f'letter-shuffle-{seed}','key':shuffled})
    targets = []
    for page in plan['targets']:
        rows = []
        for control in controls:
            result = search(page_cipher[page],control['key'],labels,probabilities,floor,selection,holdout)
            rows.append({'source':control['name'], 'source_sha256':sha(bytes(control['key'])), **result})
        targets.append({'page':page,'page_runes':len(page_cipher[page]),'searches':rows})
    planted = search(plant_cipher,key,labels,probabilities,floor,selection,holdout)
    exact_opening = ''.join(labels[i] for i in lp1[:selection])
    exact_continuation = ''.join(labels[i] for i in lp1[selection:])
    exact_at_planted_offset = ([(c-key[planted_offset+i])%29 for i,c in enumerate(plant_cipher)] == lp1)
    assert exact_at_planted_offset
    return {'schema':'liberpedia-emerson-running-key-v1','plan_sha256':sha(plan_bytes),
            'source':{'paragraphs':50,'normalized_letters':len(key),'normalized_sha256':sha(normalized.encode('ascii')),
                      'key_mapping':'A=0 through Z=25; additive modulo 29; no wrap'},
            'model':{'quadgrams':len(probabilities),'total_count':model_total,
                     'unseen_gram_log_probability':floor,'canonical_labels':labels},
            'selection_runes':selection,'holdout_runes':holdout,'targets':targets,
            'planted_control':{'source':'archived-emerson','known_page':'lp1-06','planted_offset_zero_based':planted_offset,
                               'exact_rune_recovery_at_planted_offset':exact_at_planted_offset,
                               'known_opening_score':score(exact_opening,probabilities,floor),
                               'known_continuation_score':score(exact_continuation,probabilities,floor),
                               'true_offset_selected_first':planted['top_five'][0]['offset_zero_based']==planted_offset,
                               **planted},
            'limits':'One text, mapping, arithmetic direction, scoring model, three page openings and 8 shuffled-source controls. The synthetic plant checks the search; no actual LP2 plaintext is known. Top offsets were selected only on the first 96 runes.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=report()
    if args.check:
        assert result == json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('PASS: complete Emerson running-key searches and controls reproduce')
    else:
        (HERE/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'source_letters':result['source']['normalized_letters'],
                          'planted_top':result['planted_control']['top_five'][0]['offset_zero_based'],
                          'targets':[(x['page'],[(y['source'],round(y['top_five'][0]['selection_score'],4),
                                                        round(y['top_five'][0]['continuation_score'],4)) for y in x['searches']])
                                     for x in result['targets']]}))


if __name__=='__main__':
    main()
