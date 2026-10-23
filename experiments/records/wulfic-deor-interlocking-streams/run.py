"""Audit archived P20 Deor split-stream test and run a separate calibrated diagnostic."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
N_NULL = 199
SEED = 20261023
PRIME_INDICES = {2,3,5,7,11,13,17,19,23}
ENG2GP = {'A':24,'B':17,'C':5,'D':23,'E':18,'F':0,'G':6,'H':8,'I':10,'J':11,'K':5,
          'L':20,'M':19,'N':9,'O':3,'P':13,'Q':0,'R':4,'S':15,'T':16,'U':1,'V':17,
          'W':7,'X':14,'Y':26,'Z':15}
DG_MAP = {'TH':2,'AE':25,'NG':21,'OE':22,'EO':12,'IO':27,'EA':28}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inputs():
    index = json.loads((ROOT/'data/index.json').read_text(encoding='utf-8'))
    gp = {x['rune']:i for i,x in enumerate(index['alphabet'])}
    page = (ROOT/'text/lp2-03.txt').read_bytes()
    vals = [gp[c] for c in page.decode('utf-8') if c in gp]
    assert len(vals)==217
    seq = ''.join(c for c in page.decode('utf-8') if c in gp)
    assert sha(seq.encode('utf-8'))=='56a087903b931d30a717e5595c885b14ab6cccab92d5110c894aa2b27edda3b6'
    poem = (HERE/'deor-poem-source.txt').read_bytes()
    assert sha(poem)=='be03dbfbc8d02dd6348611c973dd38ba3960c7d06833461783876546171fd143'
    text = poem.decode('utf-8').split('DEOR POEM (MODERN ENGLISH')[0].upper()
    stream=[];i=0
    while i<len(text):
        dg=text[i:i+2]
        if dg in DG_MAP:
            stream.append(DG_MAP[dg]);i+=2;continue
        if text[i] in ENG2GP:stream.append(ENG2GP[text[i]])
        i+=1
    assert len(stream)==960
    return vals,stream,{'data/index.json':sha((ROOT/'data/index.json').read_bytes()),
                        'text/lp2-03.txt':sha(page),'deor-poem-source.txt':sha(poem)}


def raw_ioc(vals):
    n=len(vals)
    if n<2:return 0.0
    c=Counter(vals)
    return sum(v*(v-1) for v in c.values())/(n*(n-1))


def split(vals):
    return ([v for v in vals if v in PRIME_INDICES],
            [v for v in vals if v not in PRIME_INDICES])


def first_decode(cipher,key,mode):
    if mode=='beaufort':return [(k-c)%29 for c,k in zip(cipher,key)]
    if mode=='sub':return [(c-k)%29 for c,k in zip(cipher,key)]
    assert mode=='add'
    return [(c+k)%29 for c,k in zip(cipher,key)]


def second_decode(cipher,key,mode):
    if mode=='sub':return [(c-k)%29 for c,k in zip(cipher,key)]
    if mode=='add':return [(c+k)%29 for c,k in zip(cipher,key)]
    assert mode=='beaufort'
    return [(k-c)%29 for c,k in zip(cipher,key)]


def complete_scan(vals,deor):
    prime,nonprime=split(vals)
    assert len(prime)==65 and len(nonprime)==152
    n_offsets=min(len(deor)-len(prime)+1,600)
    assert n_offsets==600
    best_first={'raw_ioc':-1.0}
    for mode in ('beaufort','sub','add'):
        for off in range(n_offsets):
            plain=first_decode(prime,deor[off:off+len(prime)],mode)
            score=raw_ioc(plain)
            if score>best_first['raw_ioc']:
                best_first={'mode':mode,'offset':off,'raw_ioc':score,'decoded':plain}
    selected=best_first['decoded']
    assert selected
    best_second={'raw_ioc':-1.0}
    repaired_screen_hits=0
    impossible_original_hits=0
    for mode in ('sub','add','beaufort'):
        for off in range(min(len(selected),100)):
            repeated=(selected*((len(nonprime)//len(selected))+2))[off:off+len(nonprime)]
            plain=second_decode(nonprime,repeated,mode)
            score=raw_ioc(plain)
            impossible_original_hits+=score>1.3
            repaired_screen_hits+=29*score>1.3
            if score>best_second['raw_ioc']:
                best_second={'mode':mode,'offset':off,'raw_ioc':score,'decoded':plain}
    caesar_scores=[raw_ioc([(v-shift)%29 for v in nonprime]) for shift in range(29)]
    assert all(abs(x-caesar_scores[0])<1e-15 for x in caesar_scores)
    assert impossible_original_hits==0 and max(caesar_scores)<=1.0
    return {
        'prime_runes':len(prime),'nonprime_runes':len(nonprime),
        'first_candidate_count':3*n_offsets,'second_candidate_count':3*min(len(selected),100),
        'first':{'mode':best_first['mode'],'offset':best_first['offset'],
                 'raw_ioc':best_first['raw_ioc'],'normalized_ioc':29*best_first['raw_ioc'],
                 'decoded_sha256':sha(bytes(selected))},
        'second':{'mode':best_second['mode'],'offset':best_second['offset'],
                  'raw_ioc':best_second['raw_ioc'],'normalized_ioc':29*best_second['raw_ioc'],
                  'decoded_sha256':sha(bytes(best_second['decoded']))},
        'original_second_hits':impossible_original_hits,
        'amended_second_screen_hits':repaired_screen_hits,
        'caesar_raw_ioc':caesar_scores[0],
        'caesar_normalized_ioc':29*caesar_scores[0],
        'original_caesar_hit_possible':False,
        'caesar_shift_invariant':True,
    }


def synthetic_controls():
    cipher=[2,3,5,7,11,13,17,19,23,0,1,4]
    p,np=split(cipher)
    assert len(p)==9 and len(np)==3
    key=[0,1,2,3,4,5,6,7,8]
    assert first_decode(p,key,'sub')==[(p[i]-key[i])%29 for i in range(9)]
    assert first_decode(p,key,'add')==[(p[i]+key[i])%29 for i in range(9)]
    assert first_decode(p,key,'beaufort')==[(key[i]-p[i])%29 for i in range(9)]
    repeated=(key*3)[2:5]
    for mode in ('sub','add','beaufort'):
        expected={'sub':lambda c,k:(c-k)%29,'add':lambda c,k:(c+k)%29,
                  'beaufort':lambda c,k:(k-c)%29}[mode]
        assert second_decode(np,repeated,mode)==[expected(c,k) for c,k in zip(np,repeated)]
    assert all(abs(raw_ioc([(v-shift)%29 for v in cipher])-raw_ioc(cipher))<1e-15 for shift in range(29))
    return {'partition':{'prime':9,'nonprime':3},'three_signs':True,'key_repetition':True,
            'caesar_ioc_invariance':True}


def execute():
    vals,deor,hashes=inputs()
    controls=synthetic_controls()
    observed=complete_scan(vals,deor)
    rng=random.Random(SEED)
    null=[]
    for trial in range(N_NULL):
        shuffled=vals[:]
        rng.shuffle(shuffled)
        row=complete_scan(shuffled,deor)
        null.append({'trial':trial,'first_normalized_ioc':row['first']['normalized_ioc'],
                     'second_normalized_ioc':row['second']['normalized_ioc'],
                     'amended_second_screen_hits':row['amended_second_screen_hits']})
    return {'schema':'liberpedia-wulfic-deor-interlock-results-v1',
            'input_sha256':hashes,'page':'lp2-03','source_old_page':20,'deor_gp_values':len(deor),
            'source_gate_proof':'raw IoC is in [0,1], so source >1.3 and >1.5 hits are impossible for every input',
            'synthetic_controls':controls,'observed':observed,
            'null_seed':SEED,'null_trials':N_NULL,'null':null,
            'null_second_ge_observed':sum(x['second_normalized_ioc']>=observed['second']['normalized_ioc'] for x in null),
            'null_first_ge_observed':sum(x['first_normalized_ioc']>=observed['first']['normalized_ioc'] for x in null),
            'null_screen_hits_ge_observed':sum(x['amended_second_screen_hits']>=observed['amended_second_screen_hits'] for x in null)}


def main():
    result=execute()
    path=HERE/'results.json'
    if '--check' in sys.argv:
        assert result==json.loads(path.read_text(encoding='utf-8'))
    else:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('PASS: original source arithmetic, impossible-gate audit and amended whole-procedure control')


if __name__=='__main__':main()
