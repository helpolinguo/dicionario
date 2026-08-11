import numpy as np, sys
sys.path.insert(0,'/root/dicionario/outils')
from traits import traits
from amorce import tout
T="/root/dicionario/travail"
def apprendre():
    I,C,_=tout()
    Cl=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    X=traits(np.asarray(Cl[np.sort(I)]))
    ordre=np.argsort(I)
    y=C[ordre]
    from sklearn.linear_model import LogisticRegression
    m=LogisticRegression(max_iter=3000, C=20.0)
    m.fit(X,y)
    return m
def etiqueter_groupes(m):
    moy=np.load(f"{T}/km_moy.npy")
    Xm=traits(np.clip(moy,0,255).astype(np.uint8))
    p=m.predict(Xm); pr=m.predict_proba(Xm).max(1)
    return p, pr
