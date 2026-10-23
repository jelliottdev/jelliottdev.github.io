"""Exact finite position, columnar, Caesar and Runeglish-trigram operations."""
from collections import Counter

LABELS=('F','U','TH','O','R','C','G','W','H','N','I','J','EO','P','X','S',
        'T','B','E','M','L','NG','OE','D','A','AE','Y','IO','EA')
WIDTHS=tuple(range(2,15))


def primes_below(n):
    prime=[True]*n
    if n:prime[0]=False
    if n>1:prime[1]=False
    for p in range(2,int(n**.5)+1):
        if prime[p]:
            for multiple in range(p*p,n,p):prime[multiple]=False
    return [i for i in range(n) if prime[i]]


def select(stream,origin):
    if origin=='prime0':return [stream[i] for i in primes_below(len(stream))]
    if origin=='prime1':return [stream[i-1] for i in primes_below(len(stream)+1)]
    if origin=='nonprime0':
        prime=set(primes_below(len(stream)))
        return [stream[i] for i in range(len(stream)) if i not in prime]
    raise ValueError(origin)


def columnar(stream,width):
    rows=[stream[i:i+width] for i in range(0,len(stream),width)]
    return [value for column in range(width) for row in rows if column<len(row)
            for value in (row[column],)]


def inverse_columnar(stream,width):
    rows=[list(range(i,min(i+width,len(stream)))) for i in range(0,len(stream),width)]
    result=[None]*len(stream);index=0
    for column in range(width):
        for row in rows:
            if column<len(row):
                result[row[column]]=stream[index];index+=1
    assert index==len(stream) and all(value is not None for value in result)
    return result


def ioc(stream):
    if len(stream)<2:return 0.0
    counts=Counter(stream)
    return 29*sum(count*(count-1) for count in counts.values())/(len(stream)*(len(stream)-1))


def runeglish(stream):
    return ''.join(LABELS[index] for index in stream)


def score(stream,weights):
    text=runeglish(stream)
    return sum(weights.get(text[i:i+3],0) for i in range(len(text)-2))


def stage_one(stream):
    rows={'prime1':select(stream,'prime1'),
          'prime0':select(stream,'prime0'),
          'nonprime0':select(stream,'nonprime0')}
    for width in (5,7,11,13):rows[f'whole_columnar_{width}']=columnar(stream,width)
    return rows


def stage_two(stream,weights):
    prime=select(stream,'prime0')
    constant_ioc=ioc(prime)
    rows=[]
    for width in WIDTHS:
        transposed=columnar(prime,width)
        for shift in range(29):
            plain=[(value-shift)%29 for value in transposed]
            rows.append({'width':width,'shift':shift,'trigram_score':score(plain,weights),
                         'ioc':ioc(plain),'plain':plain})
            assert abs(rows[-1]['ioc']-constant_ioc)<1e-12
    assert len(rows)==377
    rows.sort(key=lambda row:(-row['trigram_score'],-row['ioc']))
    return rows
