"""Independent Leo tests4 grid replay; upstream source code is not copied here."""
import argparse
import hashlib
import json
import random
import time
from itertools import accumulate
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
RI = {r: i for i, r in enumerate(RUNES)}


@njit
def score_grid(x, keys, modulus):
    n = len(x)
    out = np.empty((len(keys), 2), dtype=np.float64)
    for q in range(len(keys)):
        for si in range(2):
            sign = 1 if si == 0 else -1
            counts = np.zeros(29, dtype=np.int32)
            for i in range(n):
                symbol = (x[i] - sign * keys[q, i]) % modulus
                counts[symbol] += 1
            pairs = 0
            for c in counts:
                pairs += c * (c - 1)
            out[q, si] = modulus * pairs / (n * (n - 1))
    return out


def primes(count):
    ps, x = [], 2
    while len(ps) < count:
        for p in ps:
            if p * p > x:
                ps.append(x)
                break
            if x % p == 0:
                break
        else:
            ps.append(x)
        x += 1
    return ps


def fibonacci(n, a, b):
    out = []
    for _ in range(n):
        out.append(a)
        a, b = b, (a+b) % 812
        a %= 812
    return out


def sequences(pi_text):
    length = 4300
    ps = primes(length + 1)
    tot = list(range(length + 1))
    for i in range(2, length + 1):
        if tot[i] == i:
            for j in range(i, length + 1, i):
                tot[j] -= tot[j] // i
    factorial = [1]
    for i in range(1, length):
        factorial.append(factorial[-1] * i % 812)
    catalan = [1,1,2,5,14,42,132,429,1430,4862,16796,58786,208012,742900,2674440,9694845,35357670]
    arr = {
        'n': list(range(length)), 'n+1': list(range(1,length+1)),
        'n^2': [i*i for i in range(length)],
        'n^3': [i*i*i for i in range(length)],
        'tri': [i*(i+1)//2 for i in range(length)],
        'prime': ps[:length], 'prime-1': [p-1 for p in ps[:length]],
        'prime+1': [p+1 for p in ps[:length]],
        '2*prime': [2*p for p in ps[:length]],
        'prime^2': [p*p for p in ps[:length]],
        'prime_gap': [ps[i+1]-ps[i] for i in range(length)],
        'prime_cumsum': list(accumulate(ps[:length])),
        'fib': fibonacci(length,1,1), 'lucas': fibonacci(length,2,1),
        'phi(n)': tot, 'phi(prime_n)=prime-1 dup': [p-1 for p in ps[:length]],
        '2^n': [pow(2,i,812) for i in range(length)],
        '3^n': [pow(3,i,812) for i in range(length)],
        '3301*n': [3301*i for i in range(length)],
        'n*29+...': [29*i for i in range(length)],
        'prime_index_of_prime': [ps[p] for p in ps[:500]],
        'catalan': catalan*200,
        'factorial': factorial,
        'pi_digits': [int(c) for c in pi_text if c.isdigit()],
    }
    return {k:v for k,v in arr.items() if len(v)>400}


class GridBank:
    """Build each source key window once; reuse it for every shuffle.

    The source's prime-index stream has only 500 elements, and is eligible
    separately only for output streams of at most 300 symbols.
    """
    def __init__(self, seq, maxlen):
        self.base = {}
        self.prime_index = {}
        self.names = [(name,off) for name in seq if name!='prime_index_of_prime'
                      for off in range(200)]
        self.prime_names = [('prime_index_of_prime',off) for off in range(200)]
        for mod in (28,29):
            bank=np.empty((len(self.names),maxlen),dtype=np.int16)
            q=0
            for name,vals in seq.items():
                if name=='prime_index_of_prime':
                    continue
                if len(vals)<maxlen+200:
                    raise ValueError('source sequence too short for main bank: '+name)
                vec=np.asarray([v%mod for v in vals[:maxlen+200]],dtype=np.int16)
                for off in range(200):
                    bank[q,:]=vec[off:off+maxlen]
                    q+=1
            self.base[mod]=bank
            vec=np.asarray([v%mod for v in seq['prime_index_of_prime']],dtype=np.int16)
            self.prime_index[mod]=np.asarray([vec[o:o+300] for o in range(200)],dtype=np.int16)

    def score(self,x,mod):
        scores=score_grid(x,self.base[mod],mod)
        names=self.names
        if len(x)<=300:
            scores=np.vstack([scores,score_grid(x,self.prime_index[mod],mod)])
            names=names+self.prime_names
        return scores,names


def chain(x):
    return np.asarray([((int(x[i])-int(x[i-1]))%29-1)%28
                       for i in range(1,len(x)) if x[i]!=x[i-1]],dtype=np.int64)


def top_rows(scores, names, mirror=False):
    rows=[]
    for q,(name,off) in enumerate(names):
        for signi,sign in enumerate((1,-1)):
            # Complemented streams retain IoC with the opposite key sign.
            value=scores[q,1-signi] if mirror else scores[q,signi]
            rows.append((float(value),name,off,sign))
    rows.sort(reverse=True)
    return [{'ioc':round(v,6),'sequence':name,'offset':off,'sign':sign}
            for v,name,off,sign in rows[:3]],float(rows[0][0]),len(rows)


def read_inputs(source_root, text_root, plan):
    source_root, text_root=Path(source_root),Path(text_root)
    for name,want in plan['source_inputs'].items():
        if hashlib.sha256((source_root/name).read_bytes()).hexdigest()!=want:
            raise ValueError('changed source input '+name)
    for name,want in plan['text_sha256'].items():
        p=text_root/'pages'/f'{name}.txt'
        if hashlib.sha256(p.read_bytes()).hexdigest()!=want:
            raise ValueError('changed transcription '+name)
    ds=json.loads((source_root/'dataset.json').read_text(encoding='utf-8'))
    for section in ds['sections']:
        if section['name'] in plan['text_sha256']:
            text=(text_root/'pages'/f"{section['name']}.txt").read_text(encoding='utf-8')
            observed=[RI[c] for c in text if c in RI]
            if observed!=section['indices']:
                raise ValueError('dataset and transcription differ: '+section['name'])
    return ds,sequences((source_root/'pi.txt').read_text(encoding='utf-8'))


def source_arms(x,bank):
    u=chain(x)
    settings=[('forward-chain-z28',u,28,False),
              ('backward-chain-z28',u,28,True),
              ('forward-chain-z29',u,29,False),
              ('raw-z29',x,29,False),
              ('atbash-z29',x,29,True)]
    out={}
    for name,y,mod,mirror in settings:
        if mirror:
            continue
        scores,names=bank.score(y,mod)
        top,maxval,settings_count=top_rows(scores,names)
        out[name]={'stream_length':len(y),'named_settings':settings_count,
                   'top':top,'selected_max':round(maxval,6)}
        if name=='forward-chain-z28':
            mn='backward-chain-z28'
        elif name=='raw-z29':
            mn='atbash-z29'
        else:
            continue
        mtop,mmax,_=top_rows(scores,names,True)
        out[mn]={'stream_length':len(y),'named_settings':settings_count,
                 'top':mtop,'selected_max':round(mmax,6),
                 'derived_by_exact_complement':name}
    return out


def one_grid_max(x,bank):
    u=chain(x)
    best=0.0
    for y,mod in ((u,28),(u,29),(x,29)):
        scores,_=bank.score(y,mod)
        best=max(best,float(np.max(scores)))
    return best


def positive_controls(ds,seq,bank):
    plain=[v for s in ds['sections'] if s['solved'] for v in s['plain_indices']][:1200]
    if len(plain)!=1200:
        raise ValueError('not enough solved plaintext')
    prime=seq['prime']
    raw=np.asarray([(p+prime[i+47])%29 for i,p in enumerate(plain)],dtype=np.int64)
    ciphertext=[0]
    for i,p in enumerate(plain):
        ciphertext.append((ciphertext[-1]+1+(p%28+prime[i+47]%28)%28)%29)
    chained=np.asarray(ciphertext,dtype=np.int64)
    controls={}
    for label,x in [('raw',raw),('chain',chained)]:
        observed=one_grid_max(x,bank)
        rng=random.Random(330104 if label=='raw' else 330105)
        null=[]
        for _ in range(99):
            v=x.tolist()
            rng.shuffle(v)
            null.append(one_grid_max(np.asarray(v,dtype=np.int64),bank))
        controls[label]={'observed_max':round(observed,6),
                         'shuffle_maxima':[round(v,6) for v in null],
                         'exceedances':sum(v>=observed for v in null),
                         'passes_95th':sum(v>=observed for v in null)<5}
    return controls


def solved_running_key(ds):
    key=np.asarray([v%28 for s in ds['sections'] if s['solved']
                    for v in s['plain_indices']],dtype=np.int16)
    out={}
    for s in ds['sections']:
        if s['solved']:
            continue
        y=chain(np.asarray(s['indices'],dtype=np.int64))[:400]
        windows=np.asarray([key[o:o+len(y)] for o in range(len(key)-len(y))],dtype=np.int16)
        vals=score_grid(y,windows,28)
        flat=int(np.argmax(vals))
        off,signi=divmod(flat,2)
        out[s['name']]={'stream_length':len(y),'offsets':len(windows),
                        'top':{'ioc':round(float(vals[off,signi]),6),
                               'offset':off,'sign':1 if signi==0 else -1}}
    return out


def compute(source_root,text_root,plan,controls_only=False):
    ds,seq=read_inputs(source_root,text_root,plan)
    bank=GridBank(seq,max(len(s['indices']) for s in ds['sections'] if not s['solved']))
    controls=positive_controls(ds,seq,bank)
    if not all(x['passes_95th'] for x in controls.values()):
        raise ValueError('frozen planted-control gate failed; do not score LP2')
    if controls_only:
        return {'schema':'leo-tests4-controls-v1','positive_controls':controls}
    sections={}
    rng=random.Random(330104)
    for s in ds['sections']:
        if s['solved']:
            continue
        x=np.asarray(s['indices'],dtype=np.int64)
        arms=source_arms(x,bank)
        observed=max(row['selected_max'] for row in arms.values())
        null=[]
        for _ in range(99):
            v=x.tolist();rng.shuffle(v)
            null.append(one_grid_max(np.asarray(v,dtype=np.int64),bank))
        count=sum(v>=observed for v in null)
        sections[s['name']]={'source_arms':arms,'whole_grid_max':round(observed,6),
                              'shuffle_exceedances':count,'selected_grid_tail':(count+1)/100,
                              'shuffle_maxima':[round(v,6) for v in null]}
    return {'schema':'leo-tests4-sequence-replay-v1',
            'source_revision':plan['source_revision'],
            'positive_controls':controls,'sections':sections,
            'source_solved_running_key':solved_running_key(ds)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--source-root',required=True)
    ap.add_argument('--text-root',required=True)
    ap.add_argument('--controls-only',action='store_true')
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    start=time.perf_counter()
    result=compute(args.source_root,args.text_root,plan,args.controls_only)
    if args.controls_only:
        print(json.dumps(result,indent=2))
    elif args.check:
        assert result==json.loads((HERE/'results.json').read_text(encoding='utf-8'))
        print('full source grid and controls match')
    else:
        (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        print('wrote results.json')
    print('seconds:',round(time.perf_counter()-start,2))


if __name__=='__main__':
    main()
