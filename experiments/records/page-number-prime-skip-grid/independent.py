"""Independent linear-ramp decoder: only0/1 skip is mathematically admissible."""
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
counts={}
for line in (HERE/'source/liber-primus/data/english_quadgrams.txt').read_text(encoding='ascii').splitlines():
    word,count=line.split()
    counts[word]=int(count)
total=math.log10(sum(counts.values()))
MODEL={word:math.log10(count)-total for word,count in counts.items()}
FLOOR=math.log10(.01)-total


def score(text):
    return sum(MODEL.get(text[i:i+4],FLOOR) for i in range(len(text)-3))/(len(text)-3)


def decode(cipher,slope,intercept,length,width,spellings,terminal=False):
    first=(cipher[0]+intercept)%29
    states=[(0.,0,spellings[first],(first,),(0,))]
    for i in range(1,length):
        candidates=[]
        allowed=(0,1) if (cipher[i-1]-cipher[i])%29==slope else (0,)
        for cumulative,pointer,text,plain,used in states:
            for skipped in allowed:
                position=pointer+1+skipped
                p=(cipher[i]+intercept+slope*position)%29
                extended=text+spellings[p]
                delta=sum(MODEL.get(extended[end-4:end],FLOOR) for end in range(max(4,len(text)+1),len(extended)+1))
                candidates.append((cumulative+delta,position,extended,plain+(p,),used+(position,)))
        candidates.sort(key=lambda state:state[0],reverse=True)
        states=candidates[:width]
    if terminal:
        return states
    chosen=max(states,key=lambda state:state[0])
    return list(chosen[3]),chosen[2],list(chosen[4])
