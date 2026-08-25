import numpy as np, glob, os
from scipy.ndimage import gaussian_filter, shift as ndshift
DIR="/root/dicionario/work/cellules"
CH,CW=22,12
def pages():
    return [os.path.basename(p)[:-4] for p in sorted(glob.glob(DIR+"/*.npz"))]
def charger_tout():
    C=[];M=[]
    for n in pages():
        z=np.load(f"{DIR}/{n}.npz", allow_pickle=True)
        c=z['nues']; lg=z['lignes']
        occ=z['occ']
        ii,jj=np.where(occ)
        C.append(c[ii,jj])
        pg=int(n.split('-')[1])
        M.append(np.stack([np.full(len(ii),pg,np.int32), lg[ii,0].astype(np.int32), jj.astype(np.int32)],1))
    return np.concatenate(C), np.concatenate(M)
_yy,_xx=np.mgrid[0:CH,0:CW]
def traits(C, lim=2.0, sigma=0.8):
    A=C.astype(np.float32)/255.
    s=A.sum((1,2))+1e-6
    cy=(A*_yy).sum((1,2))/s; cx=(A*_xx).sum((1,2))/s
    dy=np.clip(cy-(CH-1)/2,-lim,lim); dx=np.clip(cx-(CW-1)/2,-lim,lim)
    out=np.empty_like(A)
    for i in range(len(A)): out[i]=ndshift(A[i],(-dy[i],-dx[i]),order=1,mode='constant',cval=0)
    out=gaussian_filter(out,(0,sigma,sigma))
    X=out.reshape(len(out),-1)
    X-=X.mean(1,keepdims=True)
    n=np.linalg.norm(X,axis=1,keepdims=True); n[n<1e-6]=1
    return X/n
