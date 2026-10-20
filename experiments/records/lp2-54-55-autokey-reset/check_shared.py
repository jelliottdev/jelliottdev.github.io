"""Independent controls and saved-result audit; no null resimulation."""
from collections import Counter
from itertools import product
from pathlib import Path
import argparse
import json
import random
from fractions import Fraction
from engine import transform, scan, inputs


def encrypt(plain, selected, mode, modulus):
    previous=0; cipher=[]
    for i,p in enumerate(plain):
        if i in selected:
            assert p==0
            cipher.append(0)
            if mode=='reset':previous=0
        else:
            value=(p+previous)%modulus
            cipher.append(value);previous=value
    return cipher


def direct(cipher,selected,mode):
    output=[]
    for i,c in enumerate(cipher):
        if i in selected:continue
        j=i-1
        if mode=='skip':
            while j in selected:j-=1
        previous=cipher[j] if j>=0 else 0
        output.append((c-previous)%29)
    return output


def oracle_score(output,period):
    pairs=[(a,b) for a in range(len(output)) for b in range(a+1,len(output)) if (b-a)%period==0]
    return 2*sum(output[a]==output[b] for a,b in pairs),2*len(pairs)


def controls():
    assert encrypt([1,2,0,3,4],{2},'skip',10)==[1,3,0,6,0]
    assert encrypt([1,2,0,3,4],{2},'reset',10)==[1,3,0,3,7]
    tested=0
    for cipher_tuple in product(range(3),repeat=5):
        cipher=list(cipher_tuple);zero=[i for i,c in enumerate(cipher) if c==0]
        for mask in range(1<<len(zero)):
            selected={i for j,i in enumerate(zero) if mask&(1<<j)}
            for mode in ['reset','skip']:
                output,trace=transform(cipher,selected,mode,trace=True)
                assert output==direct(cipher,selected,mode)
                assert encrypt([x['output'] for x in trace],selected,mode,29)==cipher
                for row in scan(output,[2,3,4]):
                    assert (row['numerator'],row['denominator'])==oracle_score(output,row['period'])
                tested+=1
    print('PASS:',tested,'toy mask/mode cases, adjacent/leading/trailing interrupts, inverse encryption and pairwise IoC')


def main(here):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--preflight',action='store_true');args=p.parse_args()
    controls()
    if args.preflight:return
    plan,cipher,locations=inputs(here)
    r=json.loads((here/'results.json').read_text(encoding='utf-8'))
    zeros=[i for i,c in enumerate(cipher) if c==0]
    assert r['F_positions']==zeros and r['runes']==308
    rows=[]
    for mask in range(64):
        selected={i for j,i in enumerate(zeros) if mask&(1<<j)}
        output=direct(cipher,selected,plan['mode'])
        for period in plan['periods']:
            numerator,denominator=oracle_score(output,period)
            rows.append({'mask':mask,'scored_length':len(output),'period':period,'numerator':numerator,'denominator':denominator})
    assert rows==r['observed'] and r['configurations']==1856
    best=r['maximum'];n,d=best['numerator'],best['denominator']
    assert all(x['numerator']*d<=n*x['denominator'] for x in rows)
    assert best['winners']==[{'mask':x['mask'],'period':x['period']} for x in rows if x['numerator']*d==n*x['denominator']]
    for t in r['winning_traces']:
        selected={i for j,i in enumerate(zeros) if t['mask']&(1<<j)}
        output=direct(cipher,selected,plan['mode'])
        assert [row['output'] for row in t['rows'] if row['scored_index'] is not None]==output
        assert encrypt([row['output'] for row in t['rows']],selected,plan['mode'],29)==cipher
        for i,row in enumerate(t['rows']):
            assert row['source_index']==i and row['cipher']==cipher[i]
            assert all(row[k]==v for k,v in locations[i].items())
    # Independently reconstruct and score the first two conditional null trials.
    movable=[i for i,c in enumerate(cipher) if c!=0]
    values=[cipher[i] for i in movable]
    rng=random.Random(plan['seed'])
    for expected in r['null_maxima'][:2]:
        sample=values.copy();rng.shuffle(sample)
        shuffled=cipher.copy()
        for i,v in zip(movable,sample):shuffled[i]=v
        scores=[]
        for mask in range(64):
            selected={i for j,i in enumerate(zeros) if mask&(1<<j)}
            output=direct(shuffled,selected,plan['mode'])
            for period in plan['periods']:
                numerator=denominator=0
                for residue in range(period):
                    column=output[residue::period]
                    numerator+=sum(v*(v-1) for v in Counter(column).values())
                    denominator+=len(column)*(len(column)-1)
                scores.append((mask,period,Fraction(numerator,denominator)))
        maximum=max(score for _,_,score in scores)
        assert maximum==Fraction(expected['numerator'],expected['denominator'])
        assert expected['winners']==[{'mask':mask,'period':period} for mask,period,score in scores if score==maximum]
    assert len(r['null_maxima'])==plan['trials']
    tail=sum(x['numerator']*d>=n*x['denominator'] for x in r['null_maxima'])
    assert tail==r['tail_count'] and r['p_numerator']==tail+1 and r['p_denominator']==plan['trials']+1
    assert r['p']==(tail+1)/(plan['trials']+1)
    assert r['two_mode_bonferroni_p']==min(1,2*r['p'])
    print('PASS: all 1856 observed scores by pairwise oracle, all winners/traces, two independent null searches and saved tail count')
