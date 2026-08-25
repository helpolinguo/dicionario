"""Labelling the groups: a hand-made seed + propagation by classifier."""
import sys, numpy as np, collections, pickle
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from features import feature_vector
from seed import everything
from sklearn.linear_model import LogisticRegression
T=_ROOT + "/work"
def run_step(rounds=3):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    lab=np.load(f"{T}/km_lab.npy"); mean_=np.load(f"{T}/km_moy.npy")
    I,Y,_=everything(); o=np.argsort(I); I=I[o]; Y=Y[o]
    X=feature_vector(np.asarray(C[I]))
    m=LogisticRegression(max_iter=4000,C=20.).fit(X,Y)
    Xm=feature_vector(np.clip(mean_,0,255).astype(np.uint8))
    order_=np.argsort(lab, kind='stable')
    bounds=np.searchsorted(lab[order_], np.arange(len(mean_)+1))
    for tour in range(rounds):
        pr=m.predict_proba(Xm); p=m.classes_[pr.argmax(1)]; c=pr.max(1)
        rng=np.random.default_rng(tour); idx=[];l2=[]
        surs=np.where(c>0.90)[0]
        per=max(1, min(8, 80000//max(len(surs),1)))
        for k in surs:
            mm=order_[bounds[k]:bounds[k+1]]
            if not len(mm): continue
            if len(mm)>per: mm=rng.choice(mm,per,replace=False)
            idx.append(mm); l2.append(np.full(len(mm),p[k]))
        idx=np.concatenate(idx); l2=np.concatenate(l2); o=np.argsort(idx)
        print(f"  round {tour}: {len(surs)} sure groups, {len(idx)} cells", flush=True)
        X2=np.concatenate([X,feature_vector(np.asarray(C[idx[o]]))]); Y2=np.concatenate([Y,l2[o]])
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
    # explicit hand labels (optional file)
    import os
    missing_=f"{T}/etiquettes.txt"
    nman=0
    if os.path.exists(missing_):
        for l in open(missing_, encoding='utf-8'):
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
    r=run_step()
    print(f"exactness on the seed: {100*r['exactitude']:.3f}%  ({r['amorce']} cells)")
    print(f"groups covered by the seed: {r['groupes_amorces']} ; impure: {len(r['impurs'])} ; manual: {r['manuels']}")
    print(f"median confidence {r['conf_med']:.3f} ; groups < 0.5 : {r['faibles']}")
