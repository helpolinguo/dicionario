"""Etiquetage des groupes : amorce manuelle + propagation par classifieur."""
import sys, numpy as np, collections, pickle
sys.path.insert(0,'/root/dicionario/outils')
from features import features
from seed import tout
from sklearn.linear_model import LogisticRegression
T="/root/dicionario/travail"
def executer(tours=3):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    lab=np.load(f"{T}/km_lab.npy"); moy=np.load(f"{T}/km_moy.npy")
    I,Y,_=tout(); o=np.argsort(I); I=I[o]; Y=Y[o]
    X=traits(np.asarray(C[I]))
    m=LogisticRegression(max_iter=4000,C=20.).fit(X,Y)
    Xm=traits(np.clip(moy,0,255).astype(np.uint8))
    ordre=np.argsort(lab, kind='stable')
    bornes=np.searchsorted(lab[ordre], np.arange(len(moy)+1))
    for tour in range(tours):
        pr=m.predict_proba(Xm); p=m.classes_[pr.argmax(1)]; c=pr.max(1)
        rng=np.random.default_rng(tour); idx=[];l2=[]
        surs=np.where(c>0.90)[0]
        par=max(1, min(8, 80000//max(len(surs),1)))
        for k in surs:
            mm=ordre[bornes[k]:bornes[k+1]]
            if not len(mm): continue
            if len(mm)>par: mm=rng.choice(mm,par,replace=False)
            idx.append(mm); l2.append(np.full(len(mm),p[k]))
        idx=np.concatenate(idx); l2=np.concatenate(l2); o=np.argsort(idx)
        print(f"  tour {tour}: {len(surs)} groupes surs, {len(idx)} cellules", flush=True)
        X2=np.concatenate([X,traits(np.asarray(C[idx[o]]))]); Y2=np.concatenate([Y,l2[o]])
        w=np.concatenate([np.full(len(Y),5.),np.ones(len(l2))])
        m=LogisticRegression(max_iter=2000,C=20.).fit(X2,Y2,sample_weight=w)
        del X2,Y2,w
        print(f"  tour {tour} appris", flush=True)
    pr=m.predict_proba(Xm); p=m.classes_[pr.argmax(1)].astype(object); pc=pr.max(1)
    vote=collections.defaultdict(collections.Counter)
    for k,y in zip(lab[I],Y): vote[k][y]+=1
    imp=[]
    for k,c in vote.items():
        (b,n),=c.most_common(1); p[k]=b
        if len(c)>1: imp.append((k,dict(c)))
    # etiquettes manuelles explicites (fichier facultatif)
    import os
    man=f"{T}/etiquettes.txt"
    nman=0
    if os.path.exists(man):
        for l in open(man, encoding='utf-8'):
            l=l.rstrip("\n")
            if not l.strip() or l.startswith("#"): continue
            i,_,ch=l.partition("\t"); p[int(i)]=ch; nman+=1
    np.save(f"{T}/cls_lab.npy",p); np.save(f"{T}/cls_conf.npy",pc)
    pickle.dump(m,open(f"{T}/modele.pkl","wb"))
    exact=(p[lab[I]]==Y).mean()
    return dict(exactitude=float(exact), amorce=len(I), groupes_amorces=len(vote),
                impurs=imp, manuels=nman, conf_med=float(np.median(pc)),
                faibles=int((pc<0.5).sum()))
if __name__=="__main__":
    r=executer()
    print(f"exactitude sur l'amorce : {100*r['exactitude']:.3f}%  ({r['amorce']} cellules)")
    print(f"groupes couverts par l'amorce : {r['groupes_amorces']} ; impurs : {len(r['impurs'])} ; manuels : {r['manuels']}")
    print(f"confiance mediane {r['conf_med']:.3f} ; groupes < 0.5 : {r['faibles']}")
