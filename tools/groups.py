import numpy as np, glob, os, pickle
DIR="/root/dicionario/work/cellules"
def load_(names=None):
    """Returns cells (N,22,12) uint8, meta (page,line,col) and the list of pages."""
    if names is None: names=[os.path.basename(p)[:-4] for p in sorted(glob.glob(DIR+"/*.npz"))]
    C=[]; M=[]
    for n in names:
        z=np.load(f"{DIR}/{n}.npz", allow_pickle=True)
        c=z['cells']; lg=z['lignes']
        occ = c.reshape(c.shape[0],c.shape[1],-1).max(-1) > 90
        ii,jj = np.where(occ)
        C.append(c[ii,jj])
        pg=int(n.split('-')[1])
        M.append(np.stack([np.full(len(ii),pg), lg[ii,0].astype(int), jj], axis=1))
    return np.concatenate(C), np.concatenate(M), names

def vecteurs(C):
    X=C.reshape(len(C),-1).astype(np.float32)
    X-=X.mean(1,keepdims=True)
    n=np.linalg.norm(X,axis=1,keepdims=True); n[n<1e-6]=1
    return X/n

def leaders(X, tau=0.90, order_=None, chunk=20000):
    """Grouping by greedy leader. Returns the leaders' indices and the assignment."""
    N=len(X)
    if order_ is None: order_=np.arange(N)
    aff=np.full(N,-1,dtype=np.int32); sim=np.zeros(N,dtype=np.float32)
    chefs=[]
    left_over=order_.copy()
    while len(left_over):
        i=left_over[0]; chefs.append(i); c=X[i]
        s=X[left_over]@c
        taken=s>=tau
        aff[left_over[taken]]=len(chefs)-1; sim[left_over[taken]]=s[taken]
        left_over=left_over[~taken]
    return np.array(chefs), aff, sim

def affecter(X, Cn, tau, chunk=50000):
    aff=np.empty(len(X),dtype=np.int32); sim=np.empty(len(X),dtype=np.float32)
    for a in range(0,len(X),chunk):
        s=X[a:a+chunk]@Cn.T
        aff[a:a+chunk]=s.argmax(1); sim[a:a+chunk]=s.max(1)
    aff[sim<tau]=-1
    return aff, sim
