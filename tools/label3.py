# -*- coding: utf-8 -*-
"""Relearning the labelling on the truth accumulated.

The first labelling learnt on a seed of 7,070 cells transcribed by hand over
five pages. We now hold 60,768 cells whose transcription is verified -- those
of the 8,241 headwords re-read one by one, plus the cell-by-cell corrections
-- spread over the whole book, and 734 groups whose label has been read by eye
on a sheet.

The original seed remains indispensable: the truth drawn from the headwords
contains neither a figure nor a parenthesis nor a comma. The two complete each
other.

Self-learning is kept but curbed: only the groups judged sure beyond 0.98 are
re-injected, and at most six cells per group. It was self-learning without a
safeguard that had a group of « i » labelled « space » with a confidence of
1.000.

The « space » class stays out of the learning: the cells that carry nothing
but a smudge are recognised by a geometric criterion at decoding time.
"""
import sys, os, time, collections, pickle
import numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from features2 import feature_vector2
from sklearn.neural_network import MLPClassifier
T=_ROOT + "/work"

def _lots(C, idx, taille=20000):
    """Features in slices: a million cells do not fit in memory."""
    out=[]
    for a in range(0,len(idx),taille):
        out.append(feature_vector2(np.asarray(C[idx[a:a+taille]])))
    return np.concatenate(out) if out else np.empty((0,528),np.float32)

def lire_planches():
    """Labels read by eye on the group sheets."""
    read_={}
    rep=f"{T}/groupes/rez"
    if not os.path.isdir(rep): return read_
    for f in sorted(os.listdir(rep)):
        for l in open(os.path.join(rep,f),encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "\t" not in l: continue
            a,b=l.split("\t",1)
            try: read_[int(a)]=b
            except ValueError: pass
    return read_

def run_step(rounds=3, cache=20, seuil_auto=0.98, by_group=6):
    t0=time.time()
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    kl=np.load(f"{T}/km_lab.npy"); K=int(kl.max())+1

    # --- 1. the truth: headwords re-read + cell-by-cell corrections ---
    Iv=np.load(f"{T}/gt_idx.npy"); Yv=np.load(f"{T}/gt_lab.npy",allow_pickle=True)
    # --- 2. the original seed: figures, punctuation, capitals ---
    from seed import everything
    Ia,Ya,_=everything()
    reel = Ya!=' '; Ia,Ya = Ia[reel], Ya[reel]
    # --- 3. the groups read by eye on a sheet ---
    read_=lire_planches()
    order_=np.argsort(kl,kind='stable'); bounds=np.searchsorted(kl[order_],np.arange(K+1))
    rng=np.random.default_rng(0)
    Ip=[]; Yp=[]
    for g,v in read_.items():
        if len(v)!=1 or v==' ': continue          # neither MIXITA nor ESPACO
        m=order_[bounds[g]:bounds[g+1]]
        if not len(m): continue
        e = m if len(m)<=8 else rng.choice(m,8,replace=False)
        Ip.append(e); Yp.append(np.full(len(e),v,dtype=object))
    Ip=np.concatenate(Ip) if Ip else np.empty(0,int)
    Yp=np.concatenate(Yp) if len(Yp) else np.empty(0,dtype=object)

    I=np.concatenate([Iv,Ia,Ip]); Y=np.concatenate([Yv,Ya,Yp])
    W=np.concatenate([np.full(len(Iv),1.0), np.full(len(Ia),1.0), np.full(len(Ip),0.6)])
    # a cell can appear twice: the truth prevails
    vu={}; kept=[]
    for j,(i,w) in enumerate(zip(I,W)):
        if i not in vu or w>W[vu[i]]: vu[i]=j
    kept=np.array(sorted(vu.values()))
    I,Y=I[kept],Y[kept]
    print("learning: %d cells, %d classes (truth %d, seed %d, sheets %d)"
          %(len(I),len(set(Y)),len(Iv),len(Ia),len(Ip)), flush=True)

    X=_lots(C,I)
    # voting sample, one per group
    scale=[]
    for k in range(K):
        m=order_[bounds[k]:bounds[k+1]]
        scale.append(m if len(m)<=cache else rng.choice(m,cache,replace=False))
    flats=np.sort(np.concatenate([e for e in scale if len(e)]))
    pos={v:i for i,v in enumerate(flats)}
    Xe=_lots(C,flats)
    print("feature_vector computed: %.0fs, %d voting cells"%(time.time()-t0,len(flats)), flush=True)

    m=MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-4, max_iter=40,
                    random_state=0, early_stopping=False)
    Xa,Ya2=X,Y
    for tour in range(rounds):
        m.fit(Xa,Ya2)
        P=m.predict_proba(Xe); cls=m.classes_
        label_=np.empty(K,dtype=object); conf=np.zeros(K)
        for k in range(K):
            e=scale[k]
            if not len(e): label_[k]=' '; continue
            mean_=P[[pos[v] for v in e]].mean(0)
            j=int(mean_.argmax()); label_[k]=cls[j]; conf[k]=mean_[j]
        surs=np.where(conf>seuil_auto)[0]
        print(f"  round {tour}: {len(surs)} sure groups (>{seuil_auto}), median conf {np.median(conf):.3f}  ({time.time()-t0:.0f}s)", flush=True)
        if tour==rounds-1: break
        ii=[];ll=[]
        for k in surs:
            e=scale[k]
            if len(e)>by_group: e=rng.choice(e,by_group,replace=False)
            ii.append(e); ll.append(np.full(len(e),label_[k],dtype=object))
        ii=np.concatenate(ii); ll=np.concatenate(ll)
        oo=np.argsort(ii)
        Xa=np.concatenate([X, Xe[[pos[v] for v in ii[oo]]]])
        Ya2=np.concatenate([Y, ll[oo]])
    np.save(f"{T}/cls_lab_modele.npy", label_); np.save(f"{T}/cls_conf3.npy", conf)
    pickle.dump(m, open(f"{T}/modele3.pkl","wb"))
    ex=(label_[kl[I]]==Y).mean()
    print(f"exactness of the model on the known cells: {100*ex:.3f}%", flush=True)
    return label_, conf

if __name__=="__main__": run_step()
