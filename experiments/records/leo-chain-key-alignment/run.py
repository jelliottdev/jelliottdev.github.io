"""Independent implementation of a pinned 28-state chain/sequence-key grid."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from numba import njit

HERE = Path(__file__).resolve().parent
RUNES = 'ᚠᚢᚦᚩᚱᚳᚷᚹᚻᚾᛁᛄᛇᛈᛉᛋᛏᛒᛖᛗᛚᛝᛟᛞᚪᚫᚣᛡᛠ'
RI={r:i for i,r in enumerate(RUNES)}
ROOTS=(2,3,8,10,11,14,15,18,19,21,26,27)


def primes(count):
    vals=[];n=2
    while len(vals)<count:
        if all(n%p for p in vals if p*p<=n):vals.append(n)
        n+=1
    return vals


def recurrence(n,a,b,k):
    out=[]
    for _ in range(n):
        out.append(a)
        if k=='fib':a,b=b,a+b
        elif k=='pell':a,b=b,2*b+a
    return out


def sequence_values(source_root,plan):
    n=4400;pr=primes(n);pset=set(pr)
    tot=list(range(n+1))
    for i in range(2,n+1):
        if tot[i]==i:
            for j in range(i,n+1,i):tot[j]-=tot[j]//i
    fib=recurrence(n,1,1,'fib')
    luc=recurrence(n,2,1,'fib')
    pell=[0,1]
    while len(pell)<n:pell.append(2*pell[-1]+pell[-2])
    trib=[0,0,1]
    while len(trib)<n:trib.append(sum(trib[-3:]))
    pi=source_root/'pi.txt'
    assert hashlib.sha256(pi.read_bytes()).hexdigest()==plan['pi_digits_sha256']
    digits=[int(c) for c in pi.read_text(encoding='utf-8') if c.isdigit()]
    seq={
        'n':list(range(n)),'n^2':[i*i for i in range(n)],'n^3':[i*i*i for i in range(n)],
        'tri':[i*(i+1)//2 for i in range(n)],'prime':pr,
        'prime-1':[p-1 for p in pr],'prime+1':[p+1 for p in pr],
        '2prime':[2*p for p in pr],'prime^2':[p*p for p in pr],
        'gap':[pr[i+1]-pr[i] for i in range(n-1)],
        'cumsum_prime':list(np.cumsum(np.asarray(pr,dtype=np.int64))),
        'fib':fib,'lucas':luc,'phi(n)':tot,
        '2^n':[pow(2,i,812) for i in range(n)],'3^n':[pow(3,i,812) for i in range(n)],
        '3301n':[3301*i for i in range(n)],'pi':digits,'primeidx':pr,
        'emirp':[p for p in pr if str(p)!=str(p)[::-1] and int(str(p)[::-1]) in pset],
        'twin':[p for i,p in enumerate(pr[:-1]) if pr[i+1]-p==2],
        'pell':pell,'trib':trib}
    assert list(seq)==plan['key_sequences']
    return {k:np.asarray([int(x)%28 for x in v],dtype=np.int16) for k,v in seq.items() if len(v)>=500},pr


def bijections():
    ret=[('s-1',np.asarray([-1]+[i-1 for i in range(1,29)],dtype=np.int16)),
         ('28-s',np.asarray([-1]+[28-i for i in range(1,29)],dtype=np.int16))]
    for g in ROOTS:
        vals=[-1]*29;v=1
        for e in range(28):
            vals[v]=e;v=v*g%29
        assert all(x>=0 for x in vals[1:])
        ret.append((f'dlog{g}',np.asarray(vals,dtype=np.int16)))
    return ret


def load(root,plan):
    out={}
    for name in plan['sections']:
        rel=f'pages/{name}.txt';path=root/rel
        assert hashlib.sha256(path.read_bytes()).hexdigest()==plan['section_sha256'][rel]
        out[name]=np.asarray([RI[c] for c in path.read_text(encoding='utf-8') if c in RI],dtype=np.int16)
    base=root/'data/baseline-rune-stream.txt'
    assert hashlib.sha256(base.read_bytes()).hexdigest()==plan['baseline_sha256']
    wp=[RI[c] for c in base.read_text(encoding='utf-8') if c in RI][:60000]
    assert len(wp)==60000
    return out,wp


def steps(ix):
    return np.asarray([(int(ix[i])-int(ix[i-1]))%29 for i in range(1,len(ix))][:500],dtype=np.int16)


@njit
def scan_combo(a,b,seq):
    n=len(a);m=len(b)
    best=-1.0;best_off=0;best_sign=0;best_conv=0
    # Both conventions score only nonzero differences; A retains their original
    # key positions, while B packs those positions before advancing the key.
    da=m*(m-1)/28.0;db=da
    for off in range(300):
        for sign in (1,-1):
            ca=np.zeros(28,dtype=np.int64);cb=np.zeros(28,dtype=np.int64)
            for i in range(n):
                if a[i]>=0:
                    ca[(int(a[i])-sign*int(seq[off+i]))%28]+=1
            for i in range(m):
                cb[(int(b[i])-sign*int(seq[off+i]))%28]+=1
            pa=0;pb=0
            for x in ca:pa+=x*(x-1)
            for x in cb:pb+=x*(x-1)
            va=pa/da;vb=pb/db
            if va>best:
                best=va;best_off=off;best_sign=sign;best_conv=0
            if vb>best:
                best=vb;best_off=off;best_sign=sign;best_conv=1
    return best,best_off,best_sign,best_conv


def scan(ix,seqs):
    st=steps(ix);out=[]
    best=(-1.0,None)
    for bname,bmap in bijections():
        a=bmap[st]
        b=a[a>=0]
        for sname,seq in seqs.items():
            if len(seq)<len(st)+400:
                continue
            value,off,sign,conv=scan_combo(a,b,seq)
            row={'ioc28':float(value),'sequence':sname,'offset':int(off),
                 'sign':int(sign),'bijection':bname,'convention':('A' if conv==0 else 'B')}
            out.append(row)
            if value>best[0]:best=(value,row)
    return {'steps':len(st),'nonzero_steps':int(sum(st!=0)),
            'evaluated_bijection_sequence_pairs':len(out),
            'evaluated_configurations':len(out)*300*2*2,
            'best':best[1],
            'best_by_sequence':[
                {'sequence':name,**max((x for x in out if x['sequence']==name),key=lambda x:x['ioc28'])}
                for name in seqs if any(x['sequence']==name for x in out)]}


def encrypt_control(wp,prime,consume):
    key=[p%28 for p in prime[50:]]
    out=[];prev=0;j=0
    for x in wp[:1500]:
        if x==28:
            delta=0
            if consume:j+=1
        else:
            delta=1+((x+key[j])%28);j+=1
        prev=(prev+delta)%29
        out.append(prev)
    return np.asarray(out,dtype=np.int16)


def compute(source_root,plan):
    sections,wp=load(source_root/'sources/relikd_LiberPrayground',plan)
    seqs,prime=sequence_values(source_root,plan)
    controls={str(consume).lower():scan(encrypt_control(wp,prime,consume),seqs)
              for consume in (True,False)}
    result={name:scan(sections[name],seqs) for name in plan['sections']}
    # Source printout selected this section; a conditional control only.
    rng=np.random.default_rng(plan['selected_control_seed'])
    selected=plan['sections'][-1]
    shuffled=[scan(rng.permutation(sections[selected]),seqs)['best']['ioc28']
              for _ in range(plan['selected_control_draws'])]
    observed=result[selected]['best']['ioc28']
    hits=sum(x>=observed for x in shuffled)
    return {'schema':'liberpedia-leo-chain-sequence-keys-results-v1',
            'source_revision':plan['source_revision'],
            'sequences_retained':list(seqs),
            'synthetic_controls':controls,
            'lp2_sections':result,
            'selected_section_control':{'section':selected,'seed':plan['selected_control_seed'],
              'shuffle_maxima':shuffled,'observed_best':observed,
              'exceedances':hits,'plus_one_tail':(hits+1)/(len(shuffled)+1)}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-root',type=Path,required=True,help='Pinned Leo source checkout containing pi.txt and sources/relikd_LiberPrayground')
    ap.add_argument('--check',action='store_true')
    args=ap.parse_args()
    plan=json.loads((HERE/'plan.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((args.source_root/'tests5.py').read_bytes()).hexdigest()==plan['source_test_sha256']
    assert hashlib.sha256((args.source_root/'results/tests5.txt').read_bytes()).hexdigest()==plan['source_receipt_sha256']
    result=compute(args.source_root,plan)
    path=HERE/'results.json'
    if args.check:
        assert result==json.loads(path.read_text(encoding='utf-8'))
        print('PASS: exact source chain grid, planted controls and conditional shuffles')
    else:
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'sections':{k:v['best'] for k,v in result['lp2_sections'].items()},
                          'control_hits':result['selected_section_control']['exceedances']}))


if __name__=='__main__':main()
