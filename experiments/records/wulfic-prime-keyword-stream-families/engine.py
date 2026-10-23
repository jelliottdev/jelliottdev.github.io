"""Shared GP29 operations for three pinned, finite legacy stream families."""
from collections import Counter
import hashlib
import math

import numpy as np
from numba import njit

STEPPED_VARIANTS = ('cumulative','cumulative_prime','multiplicative','prime_selector',
                    'prime_selector_mod','keyword_add_sequential','fib_recurrence','xor_position')
MODES = ('sub','add','beaufort')
GP_PRIMES = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97,101,103,107,109]
LATIN = ('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
         'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA')
QUICK_WORDS = (
    ('THE','AND','FOR','ARE','BUT','NOT','YOU','ALL','OUR','HAS','HIS','WAS','ONE','CAN','HER','OUT','NOW','WHO','WAY','OLD','ITS','MAY'),
    ('THIS','THAT','WITH','HAVE','FROM','THEY','WILL','EACH','BEEN','SAID','INTO','THAN','THEM','WHAT','WHEN','YOUR','SOME','MAKE','FIND','ONLY','KNOW','COME','SELF','JUST','LONG','MANY','TIME','LIKE'),
    ('BEING','TRUTH','WITHIN','WISDOM','SACRED','PRIMES','TOTIENT','FOLLOW','BELIEVE','NOTHING','PILGRIM','JOURNEY','THROUGH','DISCOVER','COMMAND','INSTRUCTION','DIVINITY','DEATH')
)


def primes_below(limit):
    sieve=bytearray(b'\x01')*limit
    sieve[:2]=b'\x00\x00'
    for p in range(2,math.isqrt(limit-1)+1):
        if sieve[p]:sieve[p*p:limit:p]=b'\x00'*len(range(p*p,limit,p))
    return np.fromiter((i for i,flag in enumerate(sieve) if flag),dtype=np.int64)


def first_primes(count):
    limit=120000 if count==10000 else 50000
    p=primes_below(limit)
    assert len(p)>=count
    return p[:count]


def normalized_ioc(values):
    n=len(values)
    if n<2:return 0.0
    freq=np.bincount(np.asarray(values,dtype=np.int64),minlength=29)
    return 29.0*int(np.sum(freq*(freq-1)))/(n*(n-1))


def decode(cipher,key,mode):
    cipher=np.asarray(cipher,dtype=np.int64)
    key=np.asarray(key,dtype=np.int64)
    assert len(key)>=len(cipher)
    key=key[:len(cipher)]
    if mode=='sub':return ((cipher-key)%29).astype(np.uint8)
    if mode=='add':return ((cipher+key)%29).astype(np.uint8)
    assert mode=='beaufort'
    return ((key-cipher)%29).astype(np.uint8)


def repeated(keyword,n):
    return np.resize(np.asarray(keyword,dtype=np.uint8),n)


def singleton_count(plain,positions):
    arr=np.asarray(plain)
    return sum(int(arr[p] in (10,24)) for p in positions)


def quick_score(plain):
    text=''.join(LATIN[int(i)] for i in plain)
    return sum(text.count(word)*len(word)*mult for group,mult in zip(QUICK_WORDS,(3,4,8)) for word in group)


def stream_hash(stream):
    return hashlib.sha256(np.asarray(stream,dtype=np.uint8).tobytes()).hexdigest()


@njit
def stepped_keys(keyword_rows, keyword_sizes, primes, n):
    """All source key streams at one shared maximum page length; byte identical prefix."""
    rows=keyword_rows.shape[0]*8*1001
    keys=np.zeros((rows,n),dtype=np.uint8)
    max_index=0
    for w in range(keyword_rows.shape[0]):
        size=keyword_sizes[w]
        for variant in range(8):
            for offset in range(1001):
                row=(w*8+variant)*1001+offset
                if variant==6:
                    state=np.zeros(n+offset,dtype=np.int64)
                    for j in range(size):state[j]=keyword_rows[w,j]
                    for j in range(size,n+offset):state[j]=(state[j-1]+state[j-size])%29
                    for i in range(n):keys[row,i]=state[offset+i]
                    continue
                idx=offset
                for i in range(n):
                    value=keyword_rows[w,i%size]
                    if variant==2:idx=offset+value*i
                    elif variant==3:idx=value+i+offset
                    elif variant==4:idx=value*(i+1)+offset
                    elif variant==5:idx=i+offset
                    elif variant==7:idx=(value^(i+offset))%500000
                    if idx>max_index:max_index=idx
                    assert idx<len(primes)
                    prime=primes[idx]
                    if variant in (1,4):keys[row,i]=prime%29
                    elif variant==5:keys[row,i]=(value+prime-1)%29
                    else:keys[row,i]=(prime-1)%29
                    if variant in (0,1):idx+=value
    return keys,max_index


def key_matrix(stepped_keywords, n):
    names=list(stepped_keywords)
    size=np.asarray([len(stepped_keywords[name]) for name in names],dtype=np.int64)
    widths=max(size)
    words=np.zeros((len(names),widths),dtype=np.int64)
    for i,name in enumerate(names):words[i,:size[i]]=stepped_keywords[name]
    # The source allocates 500,000 primes. Prove all actually selected indices
    # lie below the 10,000-prime prefix before replacing only its unused tail.
    primes=first_primes(10000)
    keys,max_index=stepped_keys(words,size,primes,n)
    assert max_index<10000
    return names,keys,int(max_index)


def stepped_selected(cipher,positions,keys):
    """Source all-singleton gate first, then score every surviving mode."""
    c=np.asarray(cipher,dtype=np.int64)
    positions=np.asarray(positions,dtype=np.int64)
    valid=np.ones((len(keys),3),dtype=bool)
    for position in positions:
        k=keys[:,position].astype(np.int64)
        values=((c[position]-k)%29,(c[position]+k)%29,(k-c[position])%29)
        for mode_index in range(3):
            valid[:,mode_index]&=(values[mode_index]==10)|(values[mode_index]==24)
    out=[]
    for mode_index,mode in enumerate(MODES):
        for row in np.flatnonzero(valid[:,mode_index]):
            plain=decode(c,keys[row],mode)
            score=normalized_ioc(plain)
            out.append((int(row),mode_index,score,stream_hash(plain)))
    return out


def prime_orderings(n):
    """Exactly the generators called by prime_stream_solver.test_page."""
    all_primes=primes_below(50000)
    assert len(all_primes)==5133
    seq_offsets=list(range(30))+list(range(30,500,10))+[1000,2000,3000,5000]
    ordered=[]
    for offset in seq_offsets:
        if offset+n>=len(all_primes):continue
        ordered.append((f'seq_off{offset}',all_primes[offset:offset+n]))
    ordered.append(('gp_ext',all_primes[:n]))
    fib=[0,1]
    while fib[-1]<len(all_primes):fib.append(fib[-1]+fib[-2])
    base=[int(all_primes[x]) for x in fib if x<len(all_primes)]
    ordered.append(('fib_idx',np.resize(np.asarray(base,dtype=np.int64),n)))
    spiral=[0,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987]
    ordered.append(('spiral',np.resize(all_primes[spiral],n)))
    gap_start=int(np.flatnonzero(all_primes==73)[0]);gap_end=int(np.flatnonzero(all_primes==1229)[0])
    ordered.append(('gap',np.resize(all_primes[gap_start:gap_end],n)))
    ordered.append(('rev_gp',np.concatenate((np.asarray(GP_PRIMES[::-1]),all_primes[29:n]))[:n]))
    return ordered,all_primes


def prime_key(primes,kind,all_primes):
    if kind=='totient':return ((primes-1)%29).astype(np.uint8)
    if kind=='p_mod29':return (primes%29).astype(np.uint8)
    assert kind=='idx_mod29'
    mapping={int(value):i for i,value in enumerate(all_primes)}
    return np.asarray([mapping[int(v)]%29 for v in primes],dtype=np.uint8)


def fskip_decode(cipher,key,mode):
    result=[];position=0
    for value in cipher:
        if position>=len(key):
            result.append(value);continue
        c=int(value);k=int(key[position])
        if mode=='sub':p=(c-k)%29
        elif mode=='add':p=(c+k)%29
        else:p=(k-c)%29
        result.append(p)
        if not(c==0 and p==0):position+=1
    return np.asarray(result,dtype=np.uint8)
