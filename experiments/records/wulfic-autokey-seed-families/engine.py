"""Exact GP29 affine recurrence and source-screen evaluator for autokey seeds."""
from collections import Counter
import hashlib

import numpy as np
from numba import njit

MODES=('pt_sub','pt_add','pt_beau','ct_sub','ct_add','ct_beau')


@njit
def coefficients(cipher,lag,mode):
    n=len(cipher)
    a=np.zeros(n,dtype=np.int64)
    b=np.zeros(n,dtype=np.int64)
    for i in range(n):
        if i<lag:
            if mode in (0,3):a[i]=-1;b[i]=cipher[i]
            elif mode in (1,4):a[i]=1;b[i]=cipher[i]
            else:a[i]=1;b[i]=-cipher[i]
        elif mode<3:
            if mode==0:a[i]=-a[i-lag];b[i]=cipher[i]-b[i-lag]
            elif mode==1:a[i]=a[i-lag];b[i]=cipher[i]+b[i-lag]
            else:a[i]=a[i-lag];b[i]=b[i-lag]-cipher[i]
        else:
            if mode==3:b[i]=cipher[i]-cipher[i-lag]
            elif mode==4:b[i]=cipher[i]+cipher[i-lag]
            else:b[i]=cipher[i-lag]-cipher[i]
        a[i]%=29;b[i]%=29
    return a,b


def allowed_seeds(a,b,singletons,lag):
    allowed=[set(range(29)) for _ in range(lag)]
    for pos in singletons:
        if a[pos]==0:
            if int(b[pos]) not in (10,24):
                return [set() for _ in range(lag)]
        else:
            inv=pow(int(a[pos]),-1,29)
            candidates={(target-int(b[pos]))*inv%29 for target in (10,24)}
            allowed[pos%lag]&=candidates
    return allowed


@njit
def decode_affine(a,b,seed):
    n=len(a);lag=len(seed)
    out=np.empty(n,dtype=np.uint8)
    for i in range(n):out[i]=(a[i]*seed[i%lag]+b[i])%29
    return out


@njit
def ioc_from_affine(a,b,seed,ct_suffix_frequency):
    n=len(a);lag=len(seed)
    if len(ct_suffix_frequency)==29:
        base=0
        for count in ct_suffix_frequency:base+=count*(count-1)
        extra=0
        p0=(a[0]*seed[0]+b[0])%29
        extra+=2*ct_suffix_frequency[p0]
        if lag>1:
            p1=(a[1]*seed[1]+b[1])%29
            extra+=2*ct_suffix_frequency[p1]+2*(p1==p0)
        if lag>2:
            p2=(a[2]*seed[2]+b[2])%29
            extra+=2*ct_suffix_frequency[p2]+2*(p2==p0)+2*(p2==p1)
        return 29.0*(base+extra)/(n*(n-1))
    freq=np.zeros(29,dtype=np.int64)
    for i in range(n):freq[(a[i]*seed[i%lag]+b[i])%29]+=1
    numerator=0
    for count in freq:numerator+=count*(count-1)
    return 29.0*numerator/(n*(n-1))


def suffix_frequency(b,lag,mode):
    if mode<3:return np.empty(0,dtype=np.int64)
    return np.bincount(b[lag:],minlength=29).astype(np.int64)


@njit
def exhaustive_allowed(a,b,allowed,sizes,lag,suffix):
    seed=np.zeros(3,dtype=np.int64)
    passed=0;hits=0;best=-1.0
    best_seed=np.zeros(3,dtype=np.int64)
    third=sizes[2] if lag==3 else 1
    for i in range(sizes[0]):
        seed[0]=allowed[0,i]
        for j in range(sizes[1]):
            seed[1]=allowed[1,j]
            for k in range(third):
                if lag==3:seed[2]=allowed[2,k]
                score=ioc_from_affine(a,b,seed[:lag],suffix)
                passed+=1
                if score>1.3:hits+=1
                if score>best:
                    best=score
                    best_seed[:]=seed
    return passed,hits,best,best_seed


def exhaustive(cipher,singletons,lag,mode):
    a,b=coefficients(np.asarray(cipher,dtype=np.int64),lag,mode)
    sets=allowed_seeds(a,b,singletons,lag)
    rows=np.zeros((3,29),dtype=np.int64)
    sizes=np.ones(3,dtype=np.int64)
    for residue,values in enumerate(sets):
        seq=sorted(values);sizes[residue]=len(seq);rows[residue,:len(seq)]=seq
    suffix=suffix_frequency(b,lag,mode)
    passed,hits,best,seed=exhaustive_allowed(a,b,rows,sizes,lag,suffix)
    assert passed==int(np.prod(sizes[:lag]))
    return {'gate_count':int(passed),'hit_count':int(hits),'max_ioc':None if best<0 else float(best),
            'best_seed':None if best<0 else seed[:lag].tolist()},a,b


def named(cipher,singletons,seed,mode):
    seed=np.asarray(seed,dtype=np.int64)
    a,b=coefficients(np.asarray(cipher,dtype=np.int64),len(seed),mode)
    if any((int(a[pos]*seed[pos%len(seed)]+b[pos])%29) not in (10,24) for pos in singletons):
        return None,a,b
    # The special O(k) ciphertext histogram evaluator is for exhaustive k<=3.
    plain=decode_affine(a,b,seed)
    freq=Counter(plain.tolist());n=len(plain)
    score=29*sum(count*(count-1) for count in freq.values())/(n*(n-1))
    return float(score),a,b


def output_hash(a,b,seed):
    return hashlib.sha256(decode_affine(a,b,np.asarray(seed,dtype=np.int64)).tobytes()).hexdigest()
