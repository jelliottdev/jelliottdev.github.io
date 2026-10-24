"""Prototype direct k2 source recurrence and exact sequential GP quadgram score."""
from pathlib import Path
import sys
import importlib.util
import numpy as np
from numba import njit

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'source/analysis/round12/C1'))
import feedback as source
spec=importlib.util.spec_from_file_location('original_control',HERE/'source/analysis/round12/C1/control.py')
control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
FUNCTIONS=tuple(source.F_BASIS)


def setup():
    table=np.full(26**4,source.Q.floor,dtype=np.float64)
    for gram,value in source.Q.d.items():
        code=0
        for letter in gram:code=26*code+ord(letter)-65
        table[code]=value
    letters=np.zeros((29,2),dtype=np.int64)
    lengths=np.zeros(29,dtype=np.int64)
    for i in range(29):
        label=source.gp.IDX_TO_TRANS[i];lengths[i]=len(label)
        for j,letter in enumerate(label):letters[i,j]=ord(letter)-65
    # Freeze exact pair truth tables from unchanged functions; no manual model.
    functions=np.empty((7,29,29),dtype=np.int64)
    for fi,fn in enumerate(source.F_BASIS.values()):
        for a in range(29):
            for b in range(29):functions[fi,a,b]=fn([a,b],[source.PRIMES[a],source.PRIMES[b]])
    return functions,table,letters,lengths


@njit
def decode(cipher,a,b,fi,mixed,sign,functions):
    plain=np.empty(len(cipher),dtype=np.uint8)
    for i in range(len(cipher)):
        if i<2:key=a if i==0 else b
        else:
            left=int(plain[i-2]);right=int(plain[i-1])
            if mixed:
                left=(int(cipher[i-2])+left)%29
                right=(int(cipher[i-1])+right)%29
            key=functions[fi,left,right]
        plain[i]=(int(cipher[i])+sign*key)%29
    return plain


@njit
def score(plain,table,letters,lengths):
    rolling=0;count=0;total=0.0
    for i in range(2,len(plain)):
        rune=plain[i]
        for j in range(lengths[rune]):
            rolling=26*rolling+letters[rune,j];count+=1
            if count>=4:total+=table[rolling]
            rolling%=26**3
    return total/(count-3) if count>3 else -999.0


@njit
def grid(cipher,fi,mixed,sign,functions,table,letters,lengths):
    scores=np.empty(841,dtype=np.float64)
    for a in range(29):
        for b in range(29):scores[a*29+b]=score(decode(cipher,a,b,fi,mixed,sign,functions),table,letters,lengths)
    return scores
