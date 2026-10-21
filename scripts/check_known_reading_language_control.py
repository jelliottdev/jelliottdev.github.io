"""Audit known-reading language profiles using archived traces and regex tokenization."""
from collections import Counter
import csv
from fractions import Fraction
import importlib.util
import json
from math import isclose
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/records/parallel-languages'
spec=importlib.util.spec_from_file_location('independent_words',BASE/'check.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)


def h(lengths):
    c=Counter(min(x,16) for x in lengths);return [c[i] for i in range(1,17)]


def audit(path):
    report=json.loads(path.read_bytes())
    codes=json.loads((BASE/'plan.json').read_bytes())['languages']
    modes=['letters','folded','gp-length']
    references={m:{c:h([len(w) for line in (BASE/f'{c}.dev.txt').read_text(encoding='utf-8').splitlines() for w in helper.words(line,m)]) for c in codes} for m in modes}
    alphabet={x['rune'] for x in json.loads((ROOT/'data/index.json').read_bytes())['alphabet']}
    controls=json.loads((ROOT/'data/evidence/reading-methods.json').read_bytes())['controls']
    sections={};pooled={};excluded={}
    for control in controls:
        traces=list(csv.DictReader((ROOT/f"exports/readings/{control['id']}.csv").open(encoding='utf-8')))
        derived=[];literal=[];raw=[];removed=0
        for page in control['pages']:
            source=(ROOT/f'text/{page}.txt').read_text(encoding='utf-8')
            labels=[t['latin'] for t in traces if t['page']==page];ordinal=0
            for c in source:
                if c in alphabet:derived.append(labels[ordinal]);ordinal+=1
                elif c.isalpha():removed+=1;derived.append(' ')
                else:derived.append(c)
            assert ordinal==len(labels)
            literal.append(json.loads((ROOT/f'data/pages/{page}.json').read_bytes())['reading']['literal'])
            raw.append(source)
        clean=lambda value:''.join(value).replace('/','').replace('\r','').replace('\n','')
        values={m:[len(w) for w in helper.words(clean(literal),m)] for m in modes}
        values.update({'derived-'+m:[len(w) for w in helper.words(clean(derived),m)] for m in modes})
        native=[];n=0;text=clean(raw)
        for i,c in enumerate(text):
            if c in alphabet:n+=1
            elif c=="'" and n and i+1<len(text) and text[i+1] in alphabet:continue
            else:
                if n:native.append(n);n=0
        if n:native.append(n)
        values['native-runes']=native;sections[control['id']]=values;excluded[control['id']]=removed
        for name,lengths in values.items():pooled.setdefault(name,[]).extend(lengths)
    sections['pooled']=pooled
    assert excluded==report['excluded_non_rune_alphabetic_characters']
    assert set(sections)=={r['id'] for r in report['sections']}
    for row in report['sections']:
        for name,values in sections[row['id']].items():
            actual=row['profiles'][name];hist=h(values)
            assert actual=={'tokens':len(values),'units':sum(values),'histogram':hist}
            for mode in modes if name=='native-runes' else [name.removeprefix('derived-')]:
                distances={code:sum(abs(Fraction(a,sum(hist))-Fraction(b,sum(ref))) for a,b in zip(hist,ref))/2 for code,ref in references[mode].items()}
                ranked=row['comparisons'][name+' / '+mode]
                assert {x['code'] for x in ranked}==set(codes)
                for x in ranked:assert isclose(float(distances[x['code']]),x['length_tv'],abs_tol=1e-14)
                assert [x['code'] for x in ranked]==sorted(codes,key=lambda c:distances[c])
    print('PASS: 70 profiles, 90 rankings, archived traces, excluded-character ledger and exact rational distances')


if __name__=='__main__':audit(Path(sys.argv[1]))
