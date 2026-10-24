"""Independent expectations: stdlib MT state and unbounded glibc recurrence."""
import hashlib,json,random
import run
H=run.HERE
MASK=2**32-1
def expected(mode,seed,n):
    if mode in run.MODES[:4]:
        r=random.Random(seed)
        if mode=='random29':return [int(r.random()*29) for _ in range(n)]
        if mode=='grb5_mod':return [r.getrandbits(5)%29 for _ in range(n)]
        if mode=='grb5_rej':
            out=[]
            while len(out)<n:
                x=r.getrandbits(5)
                if x<29:out.append(x)
            return out
        out=[]
        while len(out)<n:
            pool=list(range(29))
            for i in range(28,0,-1):
                j=int(r.random()*(i+1));pool[i],pool[j]=pool[j],pool[i]
            out+=pool
        return out[:n]
    if mode=='glibc_mod':
        # Different representation: keep history rather than source's ring.
        x=seed or 1;x=x if x<2**31 else x-2**32
        hist=[x]
        for _ in range(30):
            q=abs(x)//127773*(1 if x>=0 else -1)
            x=16807*(x-q*127773)-2836*q
            if x<0:x+=2147483647
            hist.append(x)
        hist+=hist[:3]
        for i in range(34,344+n):hist.append((hist[i-31]+hist[i-3])&MASK)
        return [(x>>1)%29 for x in hist[344:]]
    state=[seed]
    for i in range(1,624):state.append((1812433253*(state[-1]^(state[-1]>>30))+i)&MASK)
    if mode.startswith('php_mt_'):
        r=random.Random();r.setstate((3,tuple(state+[624]),None))
        raw=[r.getrandbits(32)>>1 for _ in range(n)]
    else:
        raw=[];cursor=624
        while len(raw)<n:
            if cursor==624:
                # Historical PHP selects the xor mask from the current word.
                for i in range(624):
                    hi=state[i];lo=state[(i+1)%624]
                    state[i]=state[(i+397)%624]^(((hi&0x80000000)|(lo&0x7fffffff))>>1)^(0x9908b0df if hi&1 else 0)
                cursor=0
            y=state[cursor];cursor+=1
            y^=y>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>18
            raw.append(y>>1)
    return [int(x*29/2**31) if mode.endswith('scale') else x%29 for x in raw]
def main():
    saved=json.loads((H/'results.json').read_text())
    cases=[(row['mode'],row['seed'],row['draws']) for row in saved['rows']]
    actual=run.compiled_streams(cases)
    for row,values,case in zip(saved['rows'],actual,cases):
        assert values==expected(*case),case
        assert hashlib.sha256(bytes(values)).hexdigest()==row['sha256']
    # Canonical MT reference, independent of the source's Python model.
    state=[5489]
    for i in range(1,624):state.append((1812433253*(state[-1]^(state[-1]>>30))+i)&MASK)
    r=random.Random();r.setstate((3,tuple(state+[624]),None))
    assert [r.getrandbits(32) for _ in range(5)]==[3499211612,581869302,3890346734,3586334585,545404204]
    assert len(actual)==136 and sum(map(len,actual))==152192
    print('PASS: independent expected streams, 152192 symbols; reference MT vector; saved digests')
if __name__=='__main__':main()
