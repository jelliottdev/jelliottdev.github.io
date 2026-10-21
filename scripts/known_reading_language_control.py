"""Run the frozen known-LP language control into a new local report.

This is preparation for review, not a published experiment record.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from reproduce_reading import reproduce, check, RUNES

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/records/parallel-languages'
PLAN=ROOT/'experiments/plans/known-reading-language-control.json'
spec=importlib.util.spec_from_file_location('language_methods',BASE/'run.py')
methods=importlib.util.module_from_spec(spec);spec.loader.exec_module(methods)


def histogram(lengths):
    counts=Counter(min(x,16) for x in lengths)
    return [counts[i] for i in range(1,17)]


def calculate():
    plan=json.loads(PLAN.read_bytes())
    for item in plan['inputs']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    codes=json.loads((BASE/'plan.json').read_bytes())['languages']
    references={}
    for mode in methods.MODES:
        references[mode]={code:histogram([len(w) for line in (BASE/f'{code}.dev.txt').read_text(encoding='utf-8').splitlines() for w in methods.tokenize(line,mode)]) for code in codes}
    sections=[];pooled={mode:[] for mode in (*methods.MODES,'native-runes')}
    controls=json.loads((ROOT/'data/evidence/reading-methods.json').read_bytes())['controls']
    for control in controls:
        decoded,_=reproduce(control,ROOT);check(decoded,ROOT)
        literal=''.join(decoded[p] for p in control['pages']).translate(str.maketrans('','','/\r\n'))
        raw=''.join((ROOT/f'text/{p}.txt').read_text(encoding='utf-8') for p in control['pages']).translate(str.maketrans('','','/\r\n'))
        lengths={mode:[len(w) for w in methods.tokenize(literal,mode)] for mode in methods.MODES}
        lengths['native-runes']=[sum(c in RUNES for c in token) for token in re.findall(f"[{RUNES}]+(?:'[{RUNES}]+)*",raw)]
        sections.append((control['id'],control['pages'],lengths))
        for mode,values in lengths.items():pooled[mode].extend(values)
    sections.append(('pooled',[p for c in controls for p in c['pages']],pooled))
    result={'plan_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'review':'Unpublished calculation; independent verification pending','sections':[]}
    for name,pages,lengths in sections:
        row={'id':name,'pages':pages,'profiles':{},'comparisons':{}}
        for representation,values in lengths.items():
            h=histogram(values)
            row['profiles'][representation]={'tokens':len(values),'units':sum(values),'histogram':h}
            corpus_modes=methods.MODES if representation=='native-runes' else [representation]
            for corpus_mode in corpus_modes:
                scores=[{'language':codes[code],'code':code,'length_tv':methods.tv(h,ref)} for code,ref in references[corpus_mode].items()]
                row['comparisons'][representation+' / '+corpus_mode]=sorted(scores,key=lambda x:x['length_tv'])
        result['sections'].append(row)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():p.error('Use a new output path; existing reports are retained.')
    result=calculate()
    with args.output.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for section in result['sections']:
        print(section['id'],section['profiles']['native-runes']['tokens'],{k:v[0]['language'] for k,v in section['comparisons'].items()})
