"""Independent k2 formulas, full decoded array, then explicit expanded-letter scoring."""
import sys,ast,math,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import numpy as np
from numba import njit
NAMES=('sum','gemsum','xor','prime_of_sum','prime_of_gemsum','lastdiff','alt_sum')

def setup(source):
    tree=ast.parse((source/'src/lp/gematria.py').read_text(encoding='utf-8'))
    rows=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='GEMATRIA' for t in n.targets)))
    labels=[row[2] for row in rows];base=np.array([row[3] for row in rows],dtype=np.int64)
    primes=np.array([i for i in range(2,2000) if all(i%d for d in range(2,math.isqrt(i)+1))],dtype=np.int64)
    assert len(primes)>218 and list(primes[:29])==list(base)
    counts={}
    for line in (source/'data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
        gram,count=line.split();counts[gram]=int(count)
    total=sum(counts.values());table=np.full(26**4,math.log10(.01)-math.log10(total),dtype=np.float64)
    for gram,count in counts.items():
        a,b,c,d=[ord(x)-65 for x in gram];table[a*17576+b*676+c*26+d]=math.log10(count)-math.log10(total)
    letters=np.full((29,2),-1,dtype=np.int64)
    for i,label in enumerate(labels):
        for j,ch in enumerate(label):letters[i,j]=ord(ch)-65
    return base,primes,letters,table

@njit
def key_value(x,y,fi,base,primes):
    if fi==0:return (x+y)%29
    if fi==1:return (base[x]+base[y])%29
    if fi==2:return (x^y)%29
    if fi==3:return primes[x+y]%29
    if fi==4:return primes[base[x]+base[y]]%29
    if fi==5:return (y-x)%29
    return (x-y)%29

@njit
def decode(C,a,b,fi,mixed,sign,base,primes):
    P=np.empty(len(C),dtype=np.int64)
    for i in range(len(C)):
        if i==0:k=a
        elif i==1:k=b
        else:
            x=P[i-2];y=P[i-1]
            if mixed:x=(x+C[i-2])%29;y=(y+C[i-1])%29
            k=key_value(x,y,fi,base,primes)
        P[i]=(C[i]+sign*k)%29
    return P

@njit
def score(P,letters,table):
    expanded=np.empty(2*len(P),dtype=np.int64);n=0
    for i in range(2,len(P)):
        expanded[n]=letters[P[i],0];n+=1
        if letters[P[i],1]>=0:expanded[n]=letters[P[i],1];n+=1
    if n<4:return -999.
    total=0.
    for j in range(n-3):total+=table[expanded[j]*17576+expanded[j+1]*676+expanded[j+2]*26+expanded[j+3]]
    return total/(n-3)

@njit
def grid(C,fi,mixed,sign,base,primes,letters,table):
    values=np.empty(841,dtype=np.float64)
    for index in range(841):values[index]=score(decode(C,index//29,index%29,fi,mixed,sign,base,primes),letters,table)
    return values
