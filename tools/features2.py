"""The features of a cell: two views concatenated.

    - registered view: the tremble of the typing (+-2 px) is absorbed;
    - raw view:        the position within the cell is kept, which
      distinguishes what registration confuses (the full stop, the
      apostrophe, the comma, the hyphen).
    """
import numpy as np
from scipy.ndimage import gaussian_filter, shift as ndshift
CH,CW=22,12
_yy,_xx=np.mgrid[0:CH,0:CW]
def feature_vector2(C, lim=2.0, sigma=0.8):
    A=C.astype(np.float32)/255.
    s=A.sum((1,2))+1e-6
    cy=(A*_yy).sum((1,2))/s; cx=(A*_xx).sum((1,2))/s
    dy=np.clip(cy-(CH-1)/2,-lim,lim); dx=np.clip(cx-(CW-1)/2,-lim,lim)
    R=np.empty_like(A)
    for i in range(len(A)): R[i]=ndshift(A[i],(-dy[i],-dx[i]),order=1,mode='constant',cval=0)
    def norm(X):
        X=X.reshape(len(X),-1); X=X-X.mean(1,keepdims=True)
        n=np.linalg.norm(X,axis=1,keepdims=True); n[n<1e-6]=1
        return X/n
    a=norm(gaussian_filter(R,(0,sigma,sigma)))
    b=norm(gaussian_filter(A,(0,sigma,sigma)))
    return np.concatenate([a, 0.7*b], axis=1)
