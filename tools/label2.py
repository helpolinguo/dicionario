"""Labelling the groups: a hand-made seed, propagation by neural network,
majority vote of the group's cells, then the primacy of the seed."""
import sys, numpy as np, collections, pickle, time
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from features2 import feature_vector2
from seed import everything
from sklearn.neural_network import MLPClassifier
T=_ROOT + "/work"

def run_step(rounds=4, cache=30, by_group=12):
    t0=time.time()
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    lab=np.load(f"{T}/km_lab.npy"); K=int(lab.max())+1
    I,Y,_=everything(); o=np.argsort(I); I=I[o]; Y=Y[o]
    # The « space » class is withdrawn from the learning: the cells that
    # contain nothing but a smudge are recognised by a geometric criterion in
    # the decoding. Letting the classifier learn a « space » class from a score
    # of examples makes the self-learning collapse: a group of « i » was
    # labelled « space » with a confidence of 1.000.
    reel = Y != ' '
    I, Y = I[reel], Y[reel]
    X=feature_vector2(np.asarray(C[I]))
    order_=np.argsort(lab,kind='stable'); bounds=np.searchsorted(lab[order_],np.arange(K+1))
    # a representative sample of each group, for the vote
    rng=np.random.default_rng(0)
    scale=[]; app=[]
    for k in range(K):
        m=order_[bounds[k]:bounds[k+1]]
        if not len(m): scale.append(np.empty(0,int)); continue
        scale.append(m if len(m)<=cache else rng.choice(m,cache,replace=False))
    flats=np.sort(np.concatenate([e for e in scale if len(e)]))
    pos={v:i for i,v in enumerate(flats)}
    Xe=feature_vector2(np.asarray(C[flats]))
    print("feature_vector: %.0fs, %d sample cells"%(time.time()-t0, len(flats)), flush=True)
    m=MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-4, max_iter=40,
                    random_state=0, early_stopping=False)
    Xa, Ya, Wa = X, Y, np.full(len(Y),1.0)
    for tour in range(rounds):
        m.fit(Xa, Ya)
        P=m.predict_proba(Xe); cls=m.classes_
        # vote by group
        label_=np.empty(K,dtype=object); conf=np.zeros(K)
        for k in range(K):
            e=scale[k]
            if not len(e): label_[k]=' '; continue
            idx=[pos[v] for v in e]
            mean_=P[idx].mean(0)
            j=int(mean_.argmax()); label_[k]=cls[j]; conf[k]=mean_[j]
        surs=np.where(conf>0.90)[0]
        print(f"  round {tour}: {len(surs)} sure groups, median conf {np.median(conf):.3f}  ({time.time()-t0:.0f}s)", flush=True)
        if tour==rounds-1: break
        idx=[];l2=[]
        for k in surs:
            e=scale[k]
            if len(e)>by_group: e=rng.choice(e,by_group,replace=False)
            idx.append(e); l2.append(np.full(len(e),label_[k]))
        idx=np.concatenate(idx); l2=np.concatenate(l2)
        oo=np.argsort(idx)
        Xa=np.concatenate([X, Xe[[pos[v] for v in idx[oo]]]])
        Ya=np.concatenate([Y, l2[oo]])
    # primacy of the seed
    vote=collections.defaultdict(collections.Counter)
    for k,y in zip(lab[I],Y): vote[k][y]+=1
    imp=0
    for k,c in vote.items():
        (b,n),=c.most_common(1); label_[k]=b
        if len(c)>1: imp+=1
    import os
    missing_=f"{T}/etiquettes.txt"; nman=0
    if os.path.exists(missing_):
        for l in open(missing_,encoding='utf-8'):
            l=l.rstrip("\n")
            if not l.strip() or l.startswith("#"): continue
            i,_,ch=l.partition("\t"); label_[int(i)]=ch; nman+=1
    np.save(f"{T}/cls_lab.npy", label_); np.save(f"{T}/cls_conf.npy", conf)
    pickle.dump(m, open(f"{T}/modele.pkl","wb"))
    ex=(label_[lab[I]]==Y).mean()
    print(f"exactness on the seed: {100*ex:.3f}%  ({len(I)} cells)", flush=True)
    print(f"groups covered: {len(vote)} ; impure: {imp} ; manual: {nman}", flush=True)
if __name__=="__main__": run_step()
