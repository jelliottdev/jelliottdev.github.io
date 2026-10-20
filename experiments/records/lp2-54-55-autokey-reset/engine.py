"""Ciphertext-feedback interruption experiment. Standard library; no network.

The two modes are explicitly declared in each record's plan. Default prints a
summary; --output saves full results without overwriting; --check repeats all
trials and compares the saved result. Null trials keep F locations fixed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[3]


def transform(cipher, selected, mode, modulus=29, trace=False):
    previous = 0
    output, ledger = [], []
    for i, value in enumerate(cipher):
        before = previous
        interrupt = i in selected
        if interrupt:
            if value != 0:
                raise ValueError('Only F=0 may be selected')
            plain = 0
            if mode == 'reset':
                previous = 0
            elif mode != 'skip':
                raise ValueError('Unknown mode')
        else:
            plain = (value - previous) % modulus
            previous = value
            output.append(plain)
        if trace:
            ledger.append({'source_index': i, 'cipher': value, 'previous_before': before,
                           'selected_F': interrupt, 'output': plain,
                           'scored_index': None if interrupt else len(output)-1,
                           'previous_after': previous})
    return output, ledger


def scan(output, periods):
    n = len(output)
    rows = []
    for period in periods:
        equal = pairs = 0
        for residue in range(period):
            counts = [0]*29
            size = 0
            for value in output[residue::period]:
                equal += 2*counts[value]
                counts[value] += 1
                size += 1
            pairs += size*(size-1)
        rows.append({'period': period, 'numerator': equal, 'denominator': pairs})
    return rows


def search(cipher, mode, periods, retain=False):
    positions = [i for i, v in enumerate(cipher) if v == 0]
    best_n, best_d, winners, cases = -1, 1, [], []
    for mask in range(1 << len(positions)):
        selected = {p for j,p in enumerate(positions) if mask & (1 << j)}
        output, _ = transform(cipher, selected, mode)
        for row in scan(output, periods):
            n,d = row['numerator'],row['denominator']
            if n*best_d > best_n*d:
                best_n,best_d,winners = n,d,[]
            if n*best_d == best_n*d:
                winners.append({'mask':mask,'period':row['period']})
            if retain:
                cases.append({'mask':mask,'scored_length':len(output),**row})
    return {'numerator':best_n,'denominator':best_d,'winners':winners}, cases


def inputs(here):
    plan = json.loads((here/'plan.json').read_text(encoding='utf-8'))
    for path,digest in plan['input_hashes'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
            raise ValueError('Input hash mismatch: '+path)
    alphabet = {a['rune']:a['index'] for a in json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))['alphabet']}
    cipher, locations = [], []
    for page in plan['pages']:
        text = (ROOT/'text'/f'{page}.txt').read_text(encoding='utf-8')
        if {c for c in text if '\u16a0'<=c<='\u16ff'}-set(alphabet):
            raise ValueError('Unknown rune')
        local = 0
        for offset,c in enumerate(text):
            if c in alphabet:
                cipher.append(alphabet[c]);locations.append({'page':page,'page_rune_index':local,'text_offset':offset})
                local += 1
    if len(cipher)!=308 or cipher.count(0)!=6:
        raise ValueError('Expected 308 runes and six Fs')
    return plan,cipher,locations


def run(here):
    plan,cipher,locations=inputs(here)
    observed,cases=search(cipher,plan['mode'],plan['periods'],True)
    f_positions=[i for i,x in enumerate(cipher) if x==0]
    movable=[i for i,x in enumerate(cipher) if x!=0]
    values=[cipher[i] for i in movable]
    rng=random.Random(plan['seed'])
    null=[]
    for trial in range(plan['trials']):
        sample=values.copy();rng.shuffle(sample)
        shuffled=cipher.copy()
        for i,v in zip(movable,sample):shuffled[i]=v
        peak,_=search(shuffled,plan['mode'],plan['periods'])
        null.append({'trial':trial+1,**peak})
        if (trial+1)%100==0:print(f"{plan['mode']}: {trial+1}/{plan['trials']} null trials",flush=True)
    tail=sum(x['numerator']*observed['denominator']>=observed['numerator']*x['denominator'] for x in null)
    traces=[]
    for mask in sorted({w['mask'] for w in observed['winners']}):
        selected={p for j,p in enumerate(f_positions) if mask&(1<<j)}
        _,ledger=transform(cipher,selected,plan['mode'],trace=True)
        traces.append({'mask':mask,'rows':[{**row,**locations[row['source_index']]} for row in ledger]})
    return {'mode':plan['mode'],'runes':len(cipher),'F_positions':f_positions,
            'plan_sha256':hashlib.sha256((here/'plan.json').read_bytes()).hexdigest(),
            'configurations':len(cases),'observed':cases,'maximum':observed,
            'winning_traces':traces,'null_maxima':null,'tail_count':tail,
            'p_numerator':tail+1,'p_denominator':plan['trials']+1,
            'p':(tail+1)/(plan['trials']+1),
            'two_mode_bonferroni_p':min(1,2*(tail+1)/(plan['trials']+1))}


def main(here):
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--output',type=Path)
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    result=run(here)
    if args.output:
        with args.output.open('x',encoding='utf-8',newline='\n') as f:
            json.dump(result,f,indent=2);f.write('\n')
    elif args.check:
        if result!=json.loads((here/'results.json').read_text(encoding='utf-8')):
            raise SystemExit('FAIL: full rerun differs')
        print('PASS: complete observed search, winning traces and all null maxima reproduce')
    print(json.dumps({k:v for k,v in result.items() if k not in ['observed','winning_traces','null_maxima']},indent=2))
