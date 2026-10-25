"""Held-out reference diagnostics, not a fitted readability cutoff or LP2 test."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata

ROOT=Path(__file__).resolve().parents[1]
CORPUS=ROOT/'experiments/records/parallel-languages'
PIN='8a5171ba8bfc5bea73e7ce7a38bca85cd99bc2175535a27e21450208dbdbaad4'

def stable(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')

def model():
    data=json.loads((ROOT/'tools/language-model.json').read_text(encoding='utf-8'))
    assert data['sha256']==PIN==hashlib.sha256(stable(data['payload'])).hexdigest()
    return data['payload']

def encode(text,payload):
    upper=unicodedata.normalize('NFD',text.upper())
    folded=''.join(c for c in upper if not unicodedata.category(c).startswith('M'))
    folded=re.sub(r"(?<=[A-Z])['’](?=[A-Z])",'',folded)
    folded=''.join(payload['encoding']['aliases'].get(c,c) for c in folded)
    out=[];index={unit:i for i,unit in enumerate(payload['alphabet'])}
    for token in re.findall('[A-Z]+',folded):
        cursor=0
        while cursor<len(token):
            match=next((unit for unit in payload['encoding']['greedyUnits'] if token[cursor:cursor+len(unit)]==unit),token[cursor])
            cursor+=len(match);out.append(index[payload['encoding']['unitAliases'].get(match,match)])
    return out

def shuffled(values,replicate):
    n=len(values);state=(0x33010000^((n*0x9e3779b1)&0xffffffff)^(((replicate+1)*0x85ebca6b)&0xffffffff))&0xffffffff
    if not state:state=1
    copy=list(values)
    for i in range(n-1,0,-1):
        state=(state^((state<<13)&0xffffffff))&0xffffffff
        state=(state^(state>>17))&0xffffffff
        state=(state^((state<<5)&0xffffffff))&0xffffffff
        j=state%(i+1);copy[i],copy[j]=copy[j],copy[i]
    return copy

def evaluate(values,payload):
    assert len(values)<=20000 and all(type(v) is int and 0<=v<29 for v in values)
    result={'runes':len(values),'windows':max(0,len(values)-2),'status':'insufficient' if len(values)<40 else 'compared','models':[]}
    if len(values)<40:return result
    def score(v,table):return sum(table[a*841+b*29+c] for a,b,c in zip(v,v[1:],v[2:]))
    controls=[shuffled(values,replicate) for replicate in range(32)]
    for item in payload['models']:
        total=score(values,item['scores']);null=[score(v,item['scores']) for v in controls]
        result['models'].append({'id':item['id'],'total':total,'shuffledMin':min(null),'shuffledMax':max(null),'shuffledAtOrAbove':sum(s>=total for s in null)})
    return result

def wrong(values,key):
    # Encrypt with the fixed DEOR repeating key; decrypt with a different key.
    true=[23,18,3,4]
    return [(v+true[i%4]-key[i%len(key)])%29 for i,v in enumerate(values)]

def calculate():
    payload=model();source_plan=json.loads((CORPUS/'plan.json').read_text(encoding='utf-8'))
    for item in source_plan['inputs']:assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    train=list(csv.DictReader((CORPUS/'metadata_dev.tsv').open(encoding='utf-8'),delimiter='\t'));test=list(csv.DictReader((CORPUS/'metadata_devtest.tsv').open(encoding='utf-8'),delimiter='\t'))
    assert not {r['URL'] for r in train}&{r['URL'] for r in test}
    codes=[m['id'] for m in payload['models']];corpus={code:(CORPUS/(code+'.devtest.txt')).read_text(encoding='utf-8').splitlines() for code in codes};assert all(len(lines)==1012 for lines in corpus.values())
    urls=defaultdict(list)
    for i,row in enumerate(test):urls[row['URL']].append(i)
    # Deterministic URL order; eight disjoint article groups. A group grows only
    # until every aligned language has >=240 encoded units, never by score.
    blocks=[];positions=[]
    for url in sorted(urls):
        positions.extend(urls[url])
        encoded={code:encode(' '.join(corpus[code][i] for i in positions),payload) for code in codes}
        if min(map(len,encoded.values()))>=240:
            blocks.append((positions,encoded));positions=[]
            if len(blocks)==8:break
    assert len(blocks)==8
    wrong_keys=[[24,19,4,5],[0,0,0,0],[1,7,13,19]];rows=[]
    for block,(indices,streams) in enumerate(blocks):
        for code in codes:
            for length in [40,80,160,240]:
                values=streams[code][:length]
                for label,output in [('correct',values),*[(f'wrong-key-{i}',wrong(values,key)) for i,key in enumerate(wrong_keys)]]:
                    rows.append({'source':'flores-devtest','block':block,'language':code,'length':length,'condition':label,'textSha256':hashlib.sha256(bytes(output)).hexdigest(),'result':evaluate(output,payload)})
    known=[];manifest=json.loads((ROOT/'exports/readings/manifest.json').read_text(encoding='utf-8'))
    for item in manifest['records']:
        path=ROOT/item['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        values=[int(row['output_index']) for row in csv.DictReader(path.open(encoding='utf-8'))]
        name=item['control']['id']
        for label,output in [('correct',values),*[(f'wrong-key-{i}',wrong(values,key)) for i,key in enumerate(wrong_keys)]]:
            known.append({'source':'native-known-LP-reading','section':name,'language':'eng_Latn','length':len(values),'condition':label,'textSha256':hashlib.sha256(bytes(output)).hexdigest(),'result':evaluate(output,payload)})
    def summarize(group):
        clean=[r for r in group if r['condition']=='correct'];neg=[r for r in group if r['condition']!='correct'];lookup={(r.get('block'),r.get('section'),r['language'],r['length']):r for r in clean}
        comparisons=[]
        for row in neg:
            original=lookup[(row.get('block'),row.get('section'),row['language'],row['length'])]
            if original['result']['status']=='insufficient':continue
            intended=row['language'];a=next(m for m in original['result']['models'] if m['id']==intended);b=next(m for m in row['result']['models'] if m['id']==intended)
            comparisons.append(a['total']>b['total'])
        return {'correct':len(clean),'wrongKey':len(neg),'intendedModelCorrectBeatsWrong':sum(comparisons),'intendedModelComparisons':len(comparisons),'correctAllEightShuffleAtOrAboveZero':sum(r['result']['status']=='compared' and all(m['shuffledAtOrAbove']==0 for m in r['result']['models']) for r in clean),'wrongAnyModelShuffleAtOrAboveZero':sum(r['result']['status']=='compared' and any(m['shuffledAtOrAbove']==0 for m in r['result']['models']) for r in neg),'insufficientCorrect':sum(r['result']['status']=='insufficient' for r in clean)}
    return {'modelSha256':PIN,'sourcePlanSha256':hashlib.sha256((CORPUS/'plan.json').read_bytes()).hexdigest(),'scriptSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'protocol':{'training':'FLORES dev only, 997 aligned sentences/language','heldout':'FLORES devtest; eight disjoint score-independent article groups, lengths40/80/160/240','trainingArticleCount':len({r['URL'] for r in train}),'heldoutArticleCount':len(urls),'articleOverlap':0,'blockSentenceIndices':[indices for indices,_ in blocks],'wrongKeys':wrong_keys,'knownReadings':'Native per-rune output_index traces; excluded from training. Historical LP spellings/transcription choices remain.','limits':['Descriptive calibration, no fitted acceptance cutoff, language identification or target LP2 scoring.','32 shuffles have coarse resolution and are not whole-search maxima.','Eight small aligned modern-prose groups and three structured wrong keys do not cover all languages, registers or ciphers.','Mechanical orthographic GP29 mapping can distort each language differently; known native LP runes need no such re-encoding.','Comparing correct/wrong pairs demonstrates these finite controls, not general recovery or false-positive power.']},'summaries':{'flores':summarize(rows),'knownLP':summarize(known),'byLength':{str(n):summarize([r for r in rows if r['length']==n]) for n in [40,80,160,240]},'byLanguage':{code:summarize([r for r in rows if r['language']==code]) for code in codes}},'rows':rows,'knownReadings':known}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--parity',action='store_true');args=p.parse_args()
    if args.parity:
        payload=model();print(json.dumps([evaluate(v,payload) for v in json.load(sys.stdin)],separators=(',',':')))
    else:
        if not args.output:p.error('--output is required for calibration')
        if args.output.exists():p.error('Choose a new output path; calibration is not overwritten')
        result=calculate();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');print(json.dumps(result['summaries'],indent=2))
