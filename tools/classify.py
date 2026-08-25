import numpy as np, sys
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from features import feature_vector
from seed import everything
T=_ROOT + "/work"
def apprendre():
    I,C,_=everything()
    Cl=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    X=feature_vector(np.asarray(Cl[np.sort(I)]))
    order_=np.argsort(I)
    y=C[order_]
    from sklearn.linear_model import LogisticRegression
    m=LogisticRegression(max_iter=3000, C=20.0)
    m.fit(X,y)
    return m
def etiqueter_groupes(m):
    mean_=np.load(f"{T}/km_moy.npy")
    Xm=feature_vector(np.clip(mean_,0,255).astype(np.uint8))
    p=m.predict(Xm); pr=m.predict_proba(Xm).max(1)
    return p, pr
