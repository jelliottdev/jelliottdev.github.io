"""Small independent scalar reference: frozen training counts, KT and closed-alphabet PPM-C."""
from collections import Counter,defaultdict
from fractions import Fraction
import math,random
ALPHABET=29

def filtered(rng,length,suppression=.83,plain=None):
    out=[]
    if plain is None:plain=[0]*length
    assert len(plain)==length
    for p in plain:
        value=(int(p)+rng.randrange(29))%29
        if out and value==out[-1] and rng.random()<suppression:value=(int(p)+rng.randrange(29))%29
        out.append(value)
    return out

def fit(pages,max_order=8,train_burnin=0):
    counts=defaultdict(Counter)
    for page in pages:
        assert all(type(x) is int and 0<=x<29 for x in page)
        for order in range(max_order+1):
            for i in range(max(order,train_burnin),len(page)):
                context=tuple(page[i-order:i]) if order else ()
                counts[context][page[i]]+=1
    return dict(counts)

def kt(model,history,symbol,order):
    context=tuple(history[-order:]) if order else ()
    counts=model.get(context,{})
    return Fraction(2*counts.get(symbol,0)+1,2*sum(counts.values())+29)

def ppm(model,history,symbol,order):
    remaining=set(range(29));mass=Fraction(1)
    for k in range(min(order,len(history)),-1,-1):
        context=tuple(history[-k:]) if k else ()
        counts={x:n for x,n in model.get(context,{}).items() if x in remaining and n>0}
        if not counts:continue
        total=sum(counts.values());distinct=len(counts)
        if distinct==len(remaining):
            assert symbol in counts
            return mass*Fraction(counts[symbol],total)
        if symbol in counts:return mass*Fraction(counts[symbol],total+distinct)
        mass*=Fraction(distinct,total+distinct)
        remaining.difference_update(counts)
    assert symbol in remaining and remaining
    return mass/Fraction(len(remaining))

def score(pages,model,kind,order,burnin=8):
    probability=kt if kind=='kt' else ppm
    total=0.;positions=0;seen=0
    for page in pages:
        for i in range(max(burnin,order),len(page)):
            history=page[max(0,i-order):i];p=probability(model,history,page[i],order)
            assert 0<p<=1
            total-=math.log2(float(p));positions+=1
            context=tuple(history[-order:]) if order else ();seen+=int(bool(model.get(context)))
    return dict(total_bits=total,positions=positions,bits_per_rune=total/positions if positions else None,trained_longest_context_positions=seen)
