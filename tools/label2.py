"""Etiquetage des groupes : amorce manuelle, propagation par reseau de neurones,
vote majoritaire des cellules du groupe, puis primaute de l'amorce."""
import sys, numpy as np, collections, pickle, time
sys.path.insert(0,'/root/dicionario/outils')
from features2 import features2
from seed import tout
from sklearn.neural_network import MLPClassifier
T="/root/dicionario/travail"

def executer(tours=4, cache=30, par_groupe=12):
    t0=time.time()
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
    lab=np.load(f"{T}/km_lab.npy"); K=int(lab.max())+1
    I,Y,_=tout(); o=np.argsort(I); I=I[o]; Y=Y[o]
    # La classe « espace » est retiree de l'apprentissage : les cellules qui ne
    # contiennent qu'une bavure sont reconnues par un critere geometrique sur
    # dans le decodage. Laisser le classifieur apprendre une classe « espace »
    # a partir d'une vingtaine d'exemples fait s'effondrer l'auto-apprentissage :
    # un groupe de « i » a ete etiquete « espace » avec une confiance de 1,000.
    reel = Y != ' '
    I, Y = I[reel], Y[reel]
    X=traits2(np.asarray(C[I]))
    ordre=np.argsort(lab,kind='stable'); bornes=np.searchsorted(lab[ordre],np.arange(K+1))
    # echantillon representatif de chaque groupe, pour le vote
    rng=np.random.default_rng(0)
    ech=[]; app=[]
    for k in range(K):
        m=ordre[bornes[k]:bornes[k+1]]
        if not len(m): ech.append(np.empty(0,int)); continue
        ech.append(m if len(m)<=cache else rng.choice(m,cache,replace=False))
    plats=np.sort(np.concatenate([e for e in ech if len(e)]))
    pos={v:i for i,v in enumerate(plats)}
    Xe=traits2(np.asarray(C[plats]))
    print("traits: %.0fs, %d cellules d'echantillon"%(time.time()-t0, len(plats)), flush=True)
    m=MLPClassifier(hidden_layer_sizes=(256,), alpha=1e-4, max_iter=40,
                    random_state=0, early_stopping=False)
    Xa, Ya, Wa = X, Y, np.full(len(Y),1.0)
    for tour in range(tours):
        m.fit(Xa, Ya)
        P=m.predict_proba(Xe); cls=m.classes_
        # vote par groupe
        etiq=np.empty(K,dtype=object); conf=np.zeros(K)
        for k in range(K):
            e=ech[k]
            if not len(e): etiq[k]=' '; continue
            idx=[pos[v] for v in e]
            moy=P[idx].mean(0)
            j=int(moy.argmax()); etiq[k]=cls[j]; conf[k]=moy[j]
        surs=np.where(conf>0.90)[0]
        print(f"  tour {tour}: {len(surs)} groupes surs, conf med {np.median(conf):.3f}  ({time.time()-t0:.0f}s)", flush=True)
        if tour==tours-1: break
        idx=[];l2=[]
        for k in surs:
            e=ech[k]
            if len(e)>par_groupe: e=rng.choice(e,par_groupe,replace=False)
            idx.append(e); l2.append(np.full(len(e),etiq[k]))
        idx=np.concatenate(idx); l2=np.concatenate(l2)
        oo=np.argsort(idx)
        Xa=np.concatenate([X, Xe[[pos[v] for v in idx[oo]]]])
        Ya=np.concatenate([Y, l2[oo]])
    # primaute de l'amorce
    vote=collections.defaultdict(collections.Counter)
    for k,y in zip(lab[I],Y): vote[k][y]+=1
    imp=0
    for k,c in vote.items():
        (b,n),=c.most_common(1); etiq[k]=b
        if len(c)>1: imp+=1
    import os
    man=f"{T}/etiquettes.txt"; nman=0
    if os.path.exists(man):
        for l in open(man,encoding='utf-8'):
            l=l.rstrip("\n")
            if not l.strip() or l.startswith("#"): continue
            i,_,ch=l.partition("\t"); etiq[int(i)]=ch; nman+=1
    np.save(f"{T}/cls_lab.npy", etiq); np.save(f"{T}/cls_conf.npy", conf)
    pickle.dump(m, open(f"{T}/modele.pkl","wb"))
    ex=(etiq[lab[I]]==Y).mean()
    print(f"exactitude sur l'amorce : {100*ex:.3f}%  ({len(I)} cellules)", flush=True)
    print(f"groupes couverts : {len(vote)} ; impurs : {imp} ; manuels : {nman}", flush=True)
if __name__=="__main__": executer()
