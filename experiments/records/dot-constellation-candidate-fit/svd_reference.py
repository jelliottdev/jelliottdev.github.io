"""Independent direct SVD least-squares reference; imports no optimized fitter."""
import itertools
import numpy as np
def all_scores(points,query):
    X=np.asarray(points,dtype=np.float64);Y=np.asarray(query,dtype=np.float64)
    permutations=np.array(list(itertools.permutations(range(5))))
    xc=X-X.mean(axis=1,keepdims=True);yc=Y-Y.mean(axis=0)
    yperm=yc[permutations];xenergy=np.sum(xc*xc,axis=(1,2));yenergy=np.sum(yc*yc)
    H=np.einsum('nki,pkj->npij',xc,yperm)
    U,S,Vh=np.linalg.svd(H)
    natural_det=np.linalg.det(U@Vh)
    outputs=[]
    for required_det in [1,-1]:
        diagonal=np.ones(S.shape);diagonal[:,:,1]=required_det*np.sign(natural_det)
        R=(U*diagonal[:,:,None,:])@Vh
        scale=np.maximum(0,np.sum(S*diagonal,axis=2)/xenergy[:,None])
        fitted=np.einsum('nki,npij->npkj',xc,R)*scale[:,:,None,None]
        residual=fitted-yperm[None,:,:,:]
        outputs.append(np.sqrt(np.sum(residual*residual,axis=(2,3))/yenergy))
    return np.stack(outputs,axis=2)
