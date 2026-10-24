"""Static held-out KT and PPM-C/exclusion. No target loading or target-specific logic."""
import math,random,lzma
import numpy as np
from numba import njit
ALPHABET=29
def filtered(length,seed,suppress=.83):
    rng=random.Random(seed);out=[]
    for _ in range(length):
        x=rng.randrange(29)
        if out and x==out[-1] and rng.random()<suppress:x=rng.randrange(29)
        out.append(x)
    return np.asarray(out,dtype=np.uint8)
def contexts(a,k,start):
    # Big-endian context code: previous k symbols, preceding the predicted symbol.
    if k==0:return np.zeros(len(a)-start,dtype=np.int64)
    windows=np.lib.stride_tricks.sliding_window_view(a,k+1)
    powers=29**np.arange(k-1,-1,-1,dtype=np.int64)
    return (windows[:,:k].astype(np.int64)@powers)[start-k:]
def query_counts(train,test):
    n=sum(max(0,len(p)-8) for p in test);q=np.zeros((n,9,29),dtype=np.int32)
    for k in range(9):
        parts=[contexts(p,k,k)*29+p[k:] for p in train if len(p)>k]
        if not parts or not n:continue
        keys=np.concatenate(parts)
        codes,freq=np.unique(keys,return_counts=True);ctx,node=np.unique(codes//29,return_inverse=True)
        table=np.zeros((len(ctx),29),dtype=np.int32);table[node,codes%29]=freq
        queries=np.concatenate([contexts(p,k,8) for p in test if len(p)>8]);idx=np.searchsorted(ctx,queries)
        valid=idx<len(ctx);valid[valid]&=ctx[idx[valid]]==queries[valid]
        q[valid,k]=table[idx[valid]]
    parts=[p[8:] for p in test if len(p)>8]
    labels=np.concatenate(parts).astype(np.int64) if parts else np.empty(0,dtype=np.int64)
    return q,labels
@njit(cache=False)
def ppm_losses(q,labels):
    n=len(labels);out=np.zeros((n,8),dtype=np.float64)
    for i in range(n):
        truth=labels[i]
        for k in range(1,9):
            mass=1.;excluded=np.int64(0);remaining=29;prob=0.
            for order in range(k,-1,-1):
                total=0;distinct=0;seen=np.int64(0)
                for symbol in range(29):
                    if excluded & (np.int64(1)<<symbol):continue
                    count=q[i,order,symbol]
                    if count:
                        total+=count;distinct+=1;seen|=np.int64(1)<<symbol
                if total==0:continue
                count=q[i,order,truth]
                if count:
                    denominator=total if distinct==remaining else total+distinct
                    prob=mass*count/denominator;break
                mass*=distinct/(total+distinct);excluded|=seen;remaining-=distinct
            if prob==0.:prob=mass/remaining
            out[i,k-1]=-math.log2(prob)
    return out
def score(pages,return_losses=False):
    pages=[np.asarray(p) for p in pages]
    if any(p.ndim!=1 or (p.size and (p.dtype.kind not in 'iu' or np.any((p<0)|(p>=29)))) for p in pages):raise ValueError('Pages must be 1D integer GP29 arrays')
    pages=[p.astype(np.uint8) for p in pages]
    n=sum(max(0,len(p)-8) for p in pages)
    if not n:raise ValueError('No held-out positions remain after burnin8')
    per_page=np.full((len(pages),16),np.nan);folds=[];all_losses=[]
    for fold in (0,1):
        ids=[j for j in range(len(pages)) if j%2==fold and len(pages[j])>8]
        train=[p for j,p in enumerate(pages) if j%2!=fold];test=[pages[j] for j in ids]
        q,y=query_counts(train,test);kt=np.empty((len(y),8),np.float64)
        for k in range(1,9):
            counts=q[:,k,:];num=counts[np.arange(len(y)),y]+.5;den=counts.sum(axis=1)+14.5
            kt[:,k-1]=-np.log2(num/den)
        losses=np.concatenate([kt,ppm_losses(q,y)],axis=1);off=0
        for j in ids:
            size=len(pages[j])-8;per_page[j]=losses[off:off+size].sum(axis=0);off+=size
        folds.append(dict(test_parity=fold,scored_positions=len(y),loss_sums=losses.sum(axis=0).tolist()))
        if return_losses:all_losses.append(losses)
    sums=np.nansum(per_page,axis=0)
    out=dict(names=[f'kt{k}' for k in range(1,9)]+[f'ppm{k}' for k in range(1,9)],bits_per_rune=(sums/n).tolist(),scored_positions=n,folds=folds,page_loss_sums=[row.tolist() if np.all(np.isfinite(row)) else None for row in per_page])
    if return_losses:out['losses']=all_losses
    return out
def pack(seq):
    # Exactly the original MDL source's minimal-width base29 representation.
    value=0
    for x in seq:value=value*29+int(x)
    return value.to_bytes((value.bit_length()+7)//8,'big')
def compression(seq):
    views={'raw1':bytes(seq),'packed':pack(seq)};out={}
    for name,data in views.items():
        encoded=lzma.compress(data,preset=9|lzma.PRESET_EXTREME)
        out[name]=dict(input_bytes=len(data),compressed_bytes=len(encoded),bits_per_rune=8*len(encoded)/len(seq))
    return out
