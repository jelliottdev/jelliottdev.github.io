"""Stable source autokey beams with explicit decoded-path key access; no target I/O."""
import numpy as np
from numba import njit
from native_probe import load
env=load();Q=env['Q'];gp=env['gp'];encode=env['eng_to_idx'];text=env['idx_to_trans'];encrypt=env['encipher_autokey']
DENSE=np.full(26**4,Q.floor,np.float64)
for word,value in Q.d.items():
    code=0
    for c in word:code=code*26+ord(c)-65
    DENSE[code]=value
LETTERS=np.zeros((29,3),np.int64);LENGTHS=np.zeros(29,np.int64)
for i in range(29):
    s=gp.IDX_TO_TRANS[i];LENGTHS[i]=len(s)
    for j,c in enumerate(s):LETTERS[i,j]=ord(c)-65
@njit(cache=False)
def keyval(t,path,primer,ct,known,mode):
    lp=len(primer)
    if t<lp:return primer[t]
    u=t-lp
    if mode==0:return path[u] if u<known else -1
    return ct[u] if u<len(ct) else 0
@njit(cache=False)
def kernel(ct,primer,sign,width,mode,dense,letters,lens):
    L=len(ct);paths=np.zeros((width,L),np.int16);ptr=np.zeros(width,np.int64);scores=np.zeros(width,np.float64);latin=np.zeros(width,np.int64);suffix=np.zeros(width,np.int64)
    k=primer[0] if len(primer) else 0;first=(ct[0]+sign*k)%29;paths[0,0]=first;latin[0]=lens[first]
    code=0
    for j in range(lens[first]):code=(code*26+letters[first,j])%(26**3)
    suffix[0]=code;count=1;last=0;need=max(len(primer)+L,4*L+8)
    for i in range(1,L):
        cap=count*4;ns=np.empty(cap,np.float64);nptr=np.empty(cap,np.int64);nlatin=np.empty(cap,np.int64);nsuffix=np.empty(cap,np.int64);parent=np.empty(cap,np.int32);runes=np.empty(cap,np.int16);used=0
        for b in range(count):
            for skip in range(4):
                accepted=ptr[b]+1+skip
                if mode==1 and accepted>=need:break
                k=keyval(accepted,paths[b],primer,ct,i,mode)
                if k<0:break
                rune=(ct[i]+sign*k)%29;valid=True
                for t in range(ptr[b]+1,accepted):
                    km=keyval(t,paths[b],primer,ct,i,mode)
                    if km<0 or (rune-sign*km)%29!=ct[i-1]:valid=False;break
                if not valid:continue
                tail=suffix[b];size=latin[b];delta=0.
                for j in range(lens[rune]):
                    full=tail*26+letters[rune,j]
                    if size>=3:delta+=dense[full]
                    tail=full%(26**3);size+=1
                ns[used]=scores[b]+delta;nptr[used]=accepted;nlatin[used]=size;nsuffix[used]=tail;parent[used]=b;runes[used]=rune;used+=1
        if used==0:break
        order=np.argsort(-ns[:used],kind='mergesort');newcount=min(width,used);nextpaths=np.zeros((width,L),np.int16)
        for b in range(newcount):
            j=order[b];p=parent[j]
            for t in range(i):nextpaths[b,t]=paths[p,t]
            nextpaths[b,i]=runes[j];scores[b]=ns[j];ptr[b]=nptr[j];latin[b]=nlatin[j];suffix[b]=nsuffix[j]
        paths=nextpaths;count=newcount;last=i
    return paths[:count,:last+1].copy(),scores[:count].copy(),ptr[:count].copy(),latin[:count].copy()
def terminals(ct,primer,sign=-1,width=450,mode='P'):
    assert len(ct)>0 and len(primer)>0
    return kernel(np.asarray(ct,np.int64),np.asarray(primer,np.int64),sign,width,0 if mode=='P' else 1,DENSE,LETTERS,LENGTHS)
def decode(ct,primer,sign=-1,width=450,mode='P'):
    paths,cum,ptr,latin=terminals(ct,primer,sign,width,mode);out=paths[0].astype(np.int64).tolist()
    return dict(score=Q.score_norm(text(out)),beam_score=float(cum[0]),plain_idx=out,translit=text(out),ptr_end=int(ptr[0]))
WORDS=('THE','DIVINITY','CIRCUMFERENCE','PRIMES','TOTIENT','INSTAR','WISDOM','PILGRIM','MOBIUS','THEPRIMESARESACRED','ANEND','EMERGENCE','SACRED','WELCOME','LOSS','SHADOW')
def primers():return [(str(i),[i]) for i in range(29)]+[(w,encode(w)) for w in WORDS]
