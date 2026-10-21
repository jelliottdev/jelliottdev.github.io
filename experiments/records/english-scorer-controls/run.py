"""Offline scorer-only controls; no external code execution or decryption."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import unicodedata

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PLAN=ROOT/'experiments/plans/english-scorer-language-controls.json'


def normalize(text,mode):
    upper=text.upper()
    transformed=upper
    if mode=='folded-ascii':
        transformed=''.join(c for c in unicodedata.normalize('NFD',upper)
                            if not unicodedata.category(c).startswith('M'))
    kept=''.join(c for c in transformed if 'A'<=c<='Z')
    return kept,{'source_characters':len(text),'uppercase_characters':len(upper),
                'after_decomposition_characters':len(transformed),'retained_letters':len(kept),
                'discarded_letters':dict(sorted(Counter(c for c in transformed if c.isalpha() and not 'A'<=c<='Z').items()))}


def load_model():
    counts={}
    for line in (HERE/'english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,n=line.split();n=int(n)
        assert len(gram)==4 and all('A'<=c<='Z' for c in gram) and n>0 and gram not in counts
        counts[gram]=n
    total=sum(counts.values());normalizer=math.log10(total)
    return {g:math.log10(n)-normalizer for g,n in counts.items()},math.log10(0.01)-normalizer,total


def produce():
    plan=json.loads(PLAN.read_bytes())
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256']
    model,floor,total=load_model()
    def score(text):
        assert len(text)>=4
        return sum(model.get(text[i:i+4],floor) for i in range(len(text)-3))/(len(text)-3)
    rows=[];normalizations=[]
    for li,code in enumerate(plan['languages']):
        lines=(ROOT/f'experiments/records/parallel-languages/{code}.devtest.txt').read_text(encoding='utf-8').splitlines()
        assert len(lines)==sum(plan['block_sentence_counts'])==1012
        start=0
        for bi,count in enumerate(plan['block_sentence_counts']):
            end=start+count;text=' '.join(lines[start:end])
            for ri,mode in enumerate(plan['representations']):
                normalized,diagnostic=normalize(text,mode)
                normalizations.append({'language':code,'block':bi,'representation':mode,
                    'sentence_start':start,'sentence_end_exclusive':end,**diagnostic})
                assert len(normalized)>=max(plan['lengths'])
                for ni,length in enumerate(plan['lengths']):
                    excerpt=normalized[:length];original=score(excerpt);controls=[]
                    for replicate in range(plan['shuffle_replicates']):
                        seed=3301000+100000*li+10000*bi+1000*ri+100*ni+replicate
                        chars=list(excerpt);random.Random(seed).shuffle(chars)
                        shuffled=''.join(chars);value=score(shuffled)
                        controls.append({'replicate':replicate,'seed':seed,'text_sha256':hashlib.sha256(shuffled.encode('ascii')).hexdigest(),
                                         'score':value,'accepted':value>=plan['threshold']})
                    scores=[c['score'] for c in controls]
                    rows.append({'language':code,'block':bi,'representation':mode,'length':length,
                        'sentence_start':start,'sentence_end_exclusive':end,'excerpt':excerpt,
                        'excerpt_sha256':hashlib.sha256(excerpt.encode('ascii')).hexdigest(),
                        'score':original,'accepted':original>=plan['threshold'],'shuffles':controls,
                        'shuffle_summary':{'minimum':min(scores),'maximum':max(scores),'mean':sum(scores)/len(scores),
                            'below_original':sum(v<original for v in scores),'equal_original':sum(v==original for v in scores),
                            'above_original':sum(v>original for v in scores)}})
            start=end
    assert len(rows)==384
    return {'status':'producer results; independent check pending','plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            'model_total_count':total,'model_quadgrams':len(model),'threshold':plan['threshold'],
            'normalizations':normalizations,'cells':rows}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--check',action='store_true');a=p.parse_args()
    if a.check and a.output:p.error('Choose --check or --output')
    dest=a.output or HERE/'results.json'
    if not a.check and dest.exists():p.error('Choose a new output path')
    r=produce()
    if a.check:assert json.loads(dest.read_bytes())==r
    else:dest.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Verified' if a.check else 'Wrote',len(r['cells']),'cells and',sum(len(c['shuffles']) for c in r['cells']),'shuffle scores')
    print(json.dumps({code:{'original_pass':sum(c['accepted'] for c in r['cells'] if c['language']==code),
                            'original_total':sum(c['language']==code for c in r['cells']),
                            'shuffle_pass':sum(s['accepted'] for c in r['cells'] if c['language']==code for s in c['shuffles'])}
                      for code in dict.fromkeys(c['language'] for c in r['cells'])}))
