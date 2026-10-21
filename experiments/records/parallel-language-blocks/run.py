"""Shorter aligned FLORES controls. Offline standard library; --check verifies results."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=HERE.parent/'parallel-languages'
spec=importlib.util.spec_from_file_location('language_baseline',BASE/'run.py')
baseline=importlib.util.module_from_spec(spec);spec.loader.exec_module(baseline)


def calculate():
    plan=json.loads((HERE/'plan.json').read_bytes())
    for x in plan['inputs']:
        assert hashlib.sha256((ROOT/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
    languages=json.loads((BASE/'plan.json').read_bytes())['languages']
    target=json.loads((ROOT/'exports/unsolved-word-tokens.json').read_bytes())
    h=Counter(min(t['rune_length'],16) for t in target)
    histogram=[h[i] for i in range(1,17)]
    spans=[];start=0
    for i in range(8):
        end=start+(127 if i<4 else 126);spans.append((start,end));start=end
    assert start==1012
    result={'plan_sha256':hashlib.sha256((HERE/'plan.json').read_bytes()).hexdigest(),
            'target_tokens':len(target),'sentence_ranges_one_based_inclusive':[[a+1,b] for a,b in spans],'modes':{}}
    for mode in baseline.MODES:
        reference={};profiles={}
        for code in languages:
            dev=(BASE/f'{code}.dev.txt').read_text(encoding='utf-8').splitlines()
            test=(BASE/f'{code}.devtest.txt').read_text(encoding='utf-8').splitlines()
            assert len(dev)==997 and len(test)==1012
            reference[code]=baseline.stats([w for line in dev for w in baseline.tokenize(line,mode)])['histogram']
            sentences=[baseline.tokenize(line,mode) for line in test]
            profiles[code]=[baseline.stats([w for line in sentences[a:b] for w in line]) for a,b in spans]
        blocks=[];confusion={c:{d:0 for d in languages} for c in languages}
        for i in range(8):
            ranking=[]
            for code in languages:
                p=profiles[code][i]
                control=sorted((baseline.tv(p['histogram'],h),c) for c,h in reference.items())
                predicted=control[0][1];confusion[code][predicted]+=1
                ranking.append({'language':languages[code],'code':code,'tokens':p['tokens'],
                    'target_size_ratio':p['tokens']/len(target),'histogram':p['histogram'],
                    'length_tv':baseline.tv(histogram,p['histogram']),
                    'control_nearest':predicted,'control_distances':control})
            ranking.sort(key=lambda x:x['length_tv'])
            blocks.append({'block':i+1,'ranking':ranking})
        result['modes'][mode]={'blocks':blocks,'confusion':confusion,
            'correct':sum(confusion[c][c] for c in languages),'total':64,
            'manuscript_best_counts':dict(Counter(b['ranking'][0]['language'] for b in blocks))}
    return result


if __name__=='__main__':
    text=json.dumps(calculate(),ensure_ascii=False,indent=2)+'\n';path=HERE/'results.json'
    if '--check' in sys.argv:assert path.read_text(encoding='utf-8')==text
    else:path.write_text(text,encoding='utf-8',newline='\n')
    r=json.loads(text)
    print(json.dumps({m:{'correct':x['correct'],'nearest_to_manuscript':x['manuscript_best_counts'],'token_range':[min(y['tokens'] for b in x['blocks'] for y in b['ranking']),max(y['tokens'] for b in x['blocks'] for y in b['ranking'])]} for m,x in r['modes'].items()},indent=2))
