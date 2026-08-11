# -*- coding: utf-8 -*-
"""Centre de chaque groupe dans l'espace de traits a deux vues.

Pour rattacher une cellule nouvelle a un groupe existant, il faut comparer
dans l'espace ou les groupes ont ete formes. Les moyennes d'images (km_moy)
ne suffisent pas : elles rendent 90 a 97 % des caracteres seulement. On
recalcule donc le centre de chaque groupe a partir de ses membres, dans
l'espace des traits a deux vues.
"""
import numpy as np, sys
sys.path.insert(0,'/root/dicionario/outils')
from traits2 import traits2
T="/root/dicionario/travail"
def executer(bloc=20000):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); kl=np.load(f"{T}/km_lab.npy")
    K=12000; D=None; S=None; n=np.zeros(K)
    for a in range(0,len(kl),bloc):
        X=traits2(np.asarray(C[a:a+bloc]))
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
