# -*- coding: utf-8 -*-
"""Table finale groupe -> caractere, par arbitrage de trois autorites.

1. La verite terrain : les cellules dont la transcription est verifiee a la
   main. Quand un groupe en contient au moins trois et qu'elles s'accordent a
   80 %, elle tranche — c'est la seule autorite qui ne soit pas une lecture.
2. La lecture a l'oeil de la planche du groupe, pour les 1 352 groupes relus.
3. Le modele reappris, partout ailleurs.

Les groupes declares « melanges » ne recoivent pas d'etiquette de groupe : ils
sont decodes cellule par cellule, puisque c'est precisement leur defaut de ne
pas etre homogenes.
"""
import numpy as np, os, sys, collections, pickle
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"

def lire_planches():
    lus={}
    for f in sorted(os.listdir(f"{T}/groupes/rez")):
        for l in open(f"{T}/groupes/rez/"+f,encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "\t" not in l: continue
            a,b=l.split("\t",1)
            try: lus[int(a)]=b
            except ValueError: pass
    return lus

def verite_par_groupe():
    kl=np.load(f"{T}/km_lab.npy")
    I=np.load(f"{T}/gt_idx.npy"); Y=np.load(f"{T}/gt_lab.npy",allow_pickle=True)
    par=collections.defaultdict(collections.Counter)
    for i,y in zip(I,Y): par[int(kl[i])][y]+=1
    return par

def executer():
    kl=np.load(f"{T}/km_lab.npy"); K=int(kl.max())+1
    mod=np.load(f"{T}/cls_lab_modele.npy",allow_pickle=True)
    lus=lire_planches(); par=verite_par_groupe()
    fin=mod.copy(); src=collections.Counter(); mixtes=[]
    for g in range(K):
        c=par.get(g); tot=sum(c.values()) if c else 0
        if c and tot>=3 and c.most_common(1)[0][1]/tot>=0.8:
            fin[g]=c.most_common(1)[0][0]; src['verite terrain']+=1; continue
        v=lus.get(g)
        if v=='ESPACO': fin[g]=' '; src['espace (planche)']+=1; continue
        if v=='MIXITA': mixtes.append(g); src['melange -> cellule par cellule']+=1; continue
        if v is not None and len(v)==1: fin[g]=v; src['planche']+=1; continue
        src['modele']+=1
    np.save(f"{T}/cls_lab.npy", fin)
    np.save(f"{T}/groupes_mixtes.npy", np.array(mixtes,dtype=int))
    print("arbitrage :", dict(src))
    anc=np.load(f"{T}/cls_lab_avant_relecture_groupes.npy",allow_pickle=True)
    n=np.bincount(kl,minlength=K)
    d=[g for g in range(K) if fin[g]!=anc[g]]
    print("groupes differents de l'etiquetage d'origine :",len(d)," cellules:",int(n[d].sum()))
    return fin, mixtes

def cellules_mixtes(mixtes, sortie=f"{T}/exceptions_modele.txt"):
    """Decodage cellule par cellule des groupes melanges."""
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); M=np.load(f"{T}/meta_all.npy")
    kl=np.load(f"{T}/km_lab.npy")
    from features2 import features2
    m=pickle.load(open(f"{T}/modele3.pkl","rb"))
    sel=np.where(np.isin(kl, mixtes))[0]
    print("cellules a decoder une a une :",len(sel))
    ecrit=0
    with open(sortie,"w",encoding='utf-8') as f:
        f.write("# Cellules des groupes melanges, decodees une a une par le modele.\n")
        f.write("# Ce fichier a la priorite la plus basse : toute correction a la main l'emporte.\n")
        for a in range(0,len(sel),20000):
            b=sel[a:a+20000]
            X=traits2(np.asarray(C[b]))
            P=m.predict_proba(X); cls=m.classes_
            j=P.argmax(1); p=P.max(1)
            for i,jj,pp in zip(b,j,p):
                if pp<0.55: continue          # trop incertain : on laisse le groupe decider
                ch=cls[jj]
                if ch==' ': continue
                pg,k,c=M[i]
                f.write(f"{int(pg)}\t{int(k)}\t{int(c)}\t{ch}\n"); ecrit+=1
    print("cellules ecrites :",ecrit)

if __name__=="__main__":
    fin,mix=executer()
    cellules_mixtes(mix)
