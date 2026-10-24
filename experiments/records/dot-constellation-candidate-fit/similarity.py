"""Exhaustive 5-point similarity fits; no LP2 input or reference-query loading."""
import itertools,json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PERMUTATIONS=np.array(list(itertools.permutations(range(5))),dtype=np.int64)
ORIENTATIONS=(1,-1)
class Library:
    def __init__(self,points,names=None):
        self.points=np.asarray(points,dtype=np.float64)
        assert self.points.ndim==3 and self.points.shape[1:]==(5,2) and np.all(np.isfinite(self.points))
        self.names=names or [str(i) for i in range(len(self.points))]
        self.mean=self.points.mean(axis=1)
        centred=self.points-self.mean[:,None,:]
        self.ss=np.sum(centred*centred,axis=(1,2));assert np.all(self.ss>0)
        self.normalized=centred/np.sqrt(self.ss)[:,None,None]
    def all_scores(self,query):
        Y=np.asarray(query,dtype=np.float64);assert Y.shape==(5,2) and np.all(np.isfinite(Y))
        centred=Y-Y.mean(axis=0);yss=float(np.sum(centred*centred));assert yss>0
        yp=(centred/np.sqrt(yss))[PERMUTATIONS]
        h=np.einsum('nki,pkj->npij',self.normalized,yp,optimize=True)
        # scale*orthogonal matrix directly: avoids dividing by zero correlation
        # and avoids cancellation in the energy-difference score near exact fits.
        a=np.stack([h[:,:,0,0]+h[:,:,1,1],h[:,:,0,0]-h[:,:,1,1]],axis=2)
        b=np.stack([h[:,:,1,0]-h[:,:,0,1],h[:,:,0,1]+h[:,:,1,0]],axis=2)
        xx=self.normalized[:,None,None,:,0];xy=self.normalized[:,None,None,:,1]
        predicted_x=a[:,:,:,None]*xx+b[:,:,:,None]*xy
        predicted_y=np.stack([-b[:,:,0,None]*xx[:,:,0,:]+a[:,:,0,None]*xy[:,:,0,:],
                               b[:,:,1,None]*xx[:,:,0,:]-a[:,:,1,None]*xy[:,:,0,:]],axis=2)
        residual_x=predicted_x-yp[None,:,None,:,0]
        residual_y=predicted_y-yp[None,:,None,:,1]
        scores=np.sqrt(np.sum(residual_x**2+residual_y**2,axis=3))
        assert scores.shape==(len(self.points),120,2)
        return scores
    def witness(self,query,candidate,permutation,orientation):
        X=self.points[candidate];Y=np.asarray(query,dtype=np.float64)[PERMUTATIONS[permutation]]
        xm=X.mean(axis=0);ym=Y.mean(axis=0);xc=X-xm;yc=Y-ym
        H=xc.T@yc;xss=float(np.sum(xc*xc));yss=float(np.sum(yc*yc))
        if orientation==0:a,b=H[0,0]+H[1,1],H[1,0]-H[0,1];scaled_R=np.array([[a,-b],[b,a]])/xss
        else:a,b=H[0,0]-H[1,1],H[0,1]+H[1,0];scaled_R=np.array([[a,b],[b,-a]])/xss
        scale=float(np.hypot(a,b)/xss);R=scaled_R/scale if scale else None
        translation=ym-xm@scaled_R;residual=X@scaled_R+translation-Y
        return {'candidate':self.names[candidate],'permutation_index':int(permutation),'star_to_query_indices':PERMUTATIONS[permutation].tolist(),'orientation':ORIENTATIONS[orientation],'scale':scale,'orthogonal_matrix':R.tolist() if R is not None else None,'rotation_radians':float(np.arctan2(R[1,0],R[0,0])) if R is not None else None,'translation':translation.tolist(),'normalized_rms':float(np.sqrt(np.sum(residual*residual)/yss)),'rms_query_units':float(np.sqrt(np.mean(np.sum(residual*residual,axis=1)))),'maximum_query_units':float(np.max(np.linalg.norm(residual,axis=1))),'residual_vectors':residual.tolist(),'zero_scale_boundary':scale==0}
def catalogue_library():
    entries=json.loads((HERE/'constellation-candidates.json').read_text(encoding='utf-8'))
    return Library([r['gnomonic_xy'] for r in entries],[r['constellation'] for r in entries])
