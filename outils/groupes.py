import numpy as np, glob, os, pickle
DIR="/root/dicionario/travail/cellules"
def charger(noms=None):
    """Retourne cells (N,22,12) uint8, meta (page,ligne,col) et la liste des pages."""
    if noms is None: noms=[os.path.basename(p)[:-4] for p in sorted(glob.glob(DIR+"/*.npz"))]
    C=[]; M=[]
    for n in noms:
        z=np.load(f"{DIR}/{n}.npz", allow_pickle=True)
        c=z['cells']; lg=z['lignes']
        occ = c.reshape(c.shape[0],c.shape[1],-1).max(-1) > 90
        ii,jj = np.where(occ)
        C.append(c[ii,jj])
        pg=int(n.split('-')[1])
        M.append(np.stack([np.full(len(ii),pg), lg[ii,0].astype(int), jj], axis=1))
    return np.concatenate(C), np.concatenate(M), noms

def vecteurs(C):
    X=C.reshape(len(C),-1).astype(np.float32)
    X-=X.mean(1,keepdims=True)
    n=np.linalg.norm(X,axis=1,keepdims=True); n[n<1e-6]=1
    return X/n

def leaders(X, tau=0.90, ordre=None, chunk=20000):
    """Regroupement par chef de file glouton. Retourne indices des chefs et affectation."""
    N=len(X)
    if ordre is None: ordre=np.arange(N)
    aff=np.full(N,-1,dtype=np.int32); sim=np.zeros(N,dtype=np.float32)
    chefs=[]
    reste=ordre.copy()
    while len(reste):
        i=reste[0]; chefs.append(i); c=X[i]
        s=X[reste]@c
        pris=s>=tau
        aff[reste[pris]]=len(chefs)-1; sim[reste[pris]]=s[pris]
        reste=reste[~pris]
    return np.array(chefs), aff, sim

def affecter(X, Cn, tau, chunk=50000):
    aff=np.empty(len(X),dtype=np.int32); sim=np.empty(len(X),dtype=np.float32)
    for a in range(0,len(X),chunk):
        s=X[a:a+chunk]@Cn.T
        aff[a:a+chunk]=s.argmax(1); sim[a:a+chunk]=s.max(1)
    aff[sim<tau]=-1
    return aff, sim
