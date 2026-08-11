# -*- coding: utf-8 -*-
"""Reapprentissage de l'etiquetage sur la verite accumulee.

Le premier etiquetage apprenait sur une amorce de 7 070 cellules transcrites a
la main sur cinq pages. On dispose maintenant de 60 768 cellules dont la
transcription est verifiee — celles des 8 241 vedettes relues une par une, plus
les corrections cellule par cellule — reparties sur tout le livre, et de 734
groupes dont l'etiquette a ete lue a l'oeil sur planche.

L'amorce d'origine reste indispensable : la verite tiree des vedettes ne
contient ni chiffre ni parenthese ni virgule. Les deux se completent.

L'auto-apprentissage est conserve mais bride : seuls les groupes juges surs
au-dela de 0,98 sont reinjectes, et six cellules au plus par groupe. C'est
l'auto-apprentissage sans garde-fou qui avait fait etiqueter « espace » un
groupe de « i » avec une confiance de 1,000.

La classe « espace » reste hors de l'apprentissage : les cellules qui ne
portent qu'une bavure sont reconnues par un critere geometrique au decodage.
"""
import sys, os, time, collections, pickle
import numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from traits2 import traits2
from sklearn.neural_network import MLPClassifier
T="/root/dicionario/travail"

def _lots(C, idx, taille=20000):
    """Traits par tranches : 1 M de cellules ne tiennent pas en memoire."""
    out=[]
    for a in range(0,len(idx),taille):
        out.append(traits2(np.asarray(C[idx[a:a+taille]])))
    return np.concatenate(out) if out else np.empty((0,528),np.float32)

def lire_planches():
    """Etiquettes lues a l'oeil sur les planches de groupes."""
    lus={}
    rep=f"{T}/groupes/rez"
    if not os.path.isdir(rep): return lus
    for f in sorted(os.listdir(rep)):
        for l in open(os.path.join(rep,f),encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "\t" not in l: continue
            a,b=l.split("\t",1)
            try: lus[int(a)]=b
            except ValueError: pass
    return lus

def executer(tours=3, cache=20, seuil_auto=0.98, par_groupe=6):
    t0=time.time()
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    kl=np.load(f"{T}/km_lab.npy"); K=int(kl.max())+1

    # --- 1. la verite : vedettes relues + corrections cellule par cellule ---
    Iv=np.load(f"{T}/gt_idx.npy"); Yv=np.load(f"{T}/gt_lab.npy",allow_pickle=True)
    # --- 2. l'amorce d'origine : chiffres, ponctuation, capitales ---
    from amorce import tout
    Ia,Ya,_=tout()
    reel = Ya!=' '; Ia,Ya = Ia[reel], Ya[reel]
    # --- 3. les groupes lus a l'oeil sur planche ---
    lus=lire_planches()
    ordre=np.argsort(kl,kind='stable'); bornes=np.searchsorted(kl[ordre],np.arange(K+1))
    rng=np.random.default_rng(0)
    Ip=[]; Yp=[]
    for g,v in lus.items():
        if len(v)!=1 or v==' ': continue          # ni MIXITA ni ESPACO
        m=ordre[bornes[g]:bornes[g+1]]
        if not len(m): continue
        e = m if len(m)<=8 else rng.choice(m,8,replace=False)
        Ip.append(e); Yp.append(np.full(len(e),v,dtype=object))
    Ip=np.concatenate(Ip) if Ip else np.empty(0,int)
    Yp=np.concatenate(Yp) if len(Yp) else np.empty(0,dtype=object)

    I=np.concatenate([Iv,Ia,Ip]); Y=np.concatenate([Yv,Ya,Yp])
    W=np.concatenate([np.full(len(Iv),1.0), np.full(len(Ia),1.0), np.full(len(Ip),0.6)])
    # une cellule peut apparaitre deux fois : la verite l'emporte
    vu={}; garde=[]
    for j,(i,w) in enumerate(zip(I,W)):
        if i not in vu or w>W[vu[i]]: vu[i]=j
    garde=np.array(sorted(vu.values()))
    I,Y=I[garde],Y[garde]
    print("apprentissage : %d cellules, %d classes (verite %d, amorce %d, planches %d)"
          %(len(I),len(set(Y)),len(Iv),len(Ia),len(Ip)), flush=True)

    X=_lots(C,I)
    # echantillon de vote, un par groupe
    ech=[]
    for k in range(K):
        m=ordre[bornes[k]:bornes[k+1]]
        ech.append(m if len(m)<=cache else rng.choice(m,cache,replace=False))
    plats=np.sort(np.concatenate([e for e in ech if len(e)]))
    pos={v:i for i,v in enumerate(plats)}
    Xe=_lots(C,plats)
    print("traits calcules : %.0fs, %d cellules de vote"%(time.time()-t0,len(plats)), flush=True)

    m=MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-4, max_iter=40,
                    random_state=0, early_stopping=False)
    Xa,Ya2=X,Y
    for tour in range(tours):
        m.fit(Xa,Ya2)
        P=m.predict_proba(Xe); cls=m.classes_
        etiq=np.empty(K,dtype=object); conf=np.zeros(K)
        for k in range(K):
            e=ech[k]
            if not len(e): etiq[k]=' '; continue
            moy=P[[pos[v] for v in e]].mean(0)
            j=int(moy.argmax()); etiq[k]=cls[j]; conf[k]=moy[j]
        surs=np.where(conf>seuil_auto)[0]
        print(f"  tour {tour}: {len(surs)} groupes surs (>{seuil_auto}), conf mediane {np.median(conf):.3f}  ({time.time()-t0:.0f}s)", flush=True)
        if tour==tours-1: break
        ii=[];ll=[]
        for k in surs:
            e=ech[k]
            if len(e)>par_groupe: e=rng.choice(e,par_groupe,replace=False)
            ii.append(e); ll.append(np.full(len(e),etiq[k],dtype=object))
        ii=np.concatenate(ii); ll=np.concatenate(ll)
        oo=np.argsort(ii)
        Xa=np.concatenate([X, Xe[[pos[v] for v in ii[oo]]]])
        Ya2=np.concatenate([Y, ll[oo]])
    np.save(f"{T}/cls_lab_modele.npy", etiq); np.save(f"{T}/cls_conf3.npy", conf)
    pickle.dump(m, open(f"{T}/modele3.pkl","wb"))
    ex=(etiq[kl[I]]==Y).mean()
    print(f"exactitude du modele sur les cellules connues : {100*ex:.3f}%", flush=True)
    return etiq, conf

if __name__=="__main__": executer()
