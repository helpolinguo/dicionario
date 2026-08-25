# -*- coding: utf-8 -*-
"""The centre of each group in the two-view feature space.

To attach a new cell to an existing group, the comparison must be made in
the space where the groups were formed. Means of images (km_moy) do not
suffice: they return only 90 to 97 % of the characters. We therefore
recompute each group's centre from its members, in the two-view feature
space.
"""
import numpy as np, sys
sys.path.insert(0,'/root/dicionario/outils')
from features2 import feature_vector2
T="/root/dicionario/travail"
def executer(bloc=20000):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); kl=np.load(f"{T}/km_lab.npy")
    K=12000; D=None; S=None; n=np.zeros(K)
    for a in range(0,len(kl),bloc):
        X=feature_vector2(np.asarray(C[a:a+bloc]))
        if S is None: D=X.shape[1]; S=np.zeros((K,D),np.float64)
        np.add.at(S, kl[a:a+bloc], X)
        np.add.at(n, kl[a:a+bloc], 1)
        if a % 200000 == 0: print("  ...%d"%a, flush=True)
    n[n==0]=1
    Q=(S/n[:,None]).astype(np.float32)
    nn=np.linalg.norm(Q,axis=1,keepdims=True); nn[nn<1e-6]=1
    np.save(f"{T}/km_centres2.npy", Q/nn)
    print("centres ecrits :", Q.shape)
if __name__=="__main__": executer()
