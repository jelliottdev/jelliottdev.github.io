"""Symmetric finite-reference max-Z comparison; no RNG, fitting choices or targets."""
import numpy as np
def compare(reference,candidate,tails):
    reference=np.asarray(reference,dtype=np.float64);candidate=np.asarray(candidate,dtype=np.float64)
    if reference.ndim!=2 or candidate.shape!=(reference.shape[1],) or len(tails)!=reference.shape[1]:raise ValueError('Metric dimensions differ')
    if not np.all(np.isfinite(reference)) or not np.all(np.isfinite(candidate)) or any(x not in ('lower','upper') for x in tails):raise ValueError('Invalid metrics/tails')
    # Include every row symmetrically in scaling. Candidate is simply the last row.
    data=np.vstack([reference,candidate]);direction=np.array([-1 if t=='lower' else 1 for t in tails]);oriented=data*direction
    mean=oriented.mean(axis=0);sd=oriented.std(axis=0,ddof=0)
    constant=np.all(oriented==oriented[0],axis=0)
    if np.any((~constant)&(sd==0)):raise ValueError('Nonconstant metric scale underflow')
    z=np.divide(oriented-mean,sd,out=np.zeros_like(oriented),where=(sd>0)&(~constant))
    scores=z.max(axis=1);rank=int(np.count_nonzero(scores>=scores[-1]))
    marginal_ranks=1+np.count_nonzero(reference*direction>=candidate*direction,axis=0)
    marginal_threshold=np.quantile(reference*direction,.99,axis=0,method='linear')
    marginal_pass=(candidate*direction)>marginal_threshold
    fraction=rank/len(data)
    return dict(family_rank=rank,family_reference_rows=len(data),family_rank_fraction=fraction,max_z=float(scores[-1]),reference_max_z=scores[:-1].tolist(),marginal_rank=marginal_ranks.tolist(),marginal_reference_fraction=(marginal_ranks/len(data)).tolist(),marginal_strict_1percent_flags=marginal_pass.tolist(),gate=bool(fraction<.01 and np.any(marginal_pass)),constant_metrics=np.flatnonzero(constant).tolist())
