# -*- coding: utf-8 -*-
"""The final table group -> character, by arbitration between three authorities.

1. The ground truth: the cells whose transcription is verified by hand. When a
   group holds at least three of them and they agree to 80 %, it settles the
   matter -- it is the only authority that is not a reading.
2. The reading by eye of the group's sheet, for the 1,352 groups re-read.
3. The re-learnt model, everywhere else.

Groups declared « mixed » receive no group label: they are decoded cell by
cell, since not being homogeneous is precisely their defect.
"""
import numpy as np, os, sys, collections, pickle
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"

def lire_planches():
    read_={}
    for f in sorted(os.listdir(f"{T}/groupes/rez")):
        for l in open(f"{T}/groupes/rez/"+f,encoding='utf-8'):
            l=l.rstrip("\n")
            if l.startswith("==") or "\t" not in l: continue
            a,b=l.split("\t",1)
            try: read_[int(a)]=b
            except ValueError: pass
    return read_

def verite_par_groupe():
    kl=np.load(f"{T}/km_lab.npy")
    I=np.load(f"{T}/gt_idx.npy"); Y=np.load(f"{T}/gt_lab.npy",allow_pickle=True)
    per=collections.defaultdict(collections.Counter)
    for i,y in zip(I,Y): per[int(kl[i])][y]+=1
    return per

def run_step():
    kl=np.load(f"{T}/km_lab.npy"); K=int(kl.max())+1
    mod=np.load(f"{T}/cls_lab_modele.npy",allow_pickle=True)
    read_=lire_planches(); per=verite_par_groupe()
    end_=mod.copy(); src=collections.Counter(); mixtes=[]
    for g in range(K):
        c=per.get(g); tot=sum(c.values()) if c else 0
        if c and tot>=3 and c.most_common(1)[0][1]/tot>=0.8:
            end_[g]=c.most_common(1)[0][0]; src['verite terrain']+=1; continue
        v=read_.get(g)
        if v=='ESPACO': end_[g]=' '; src['espace (planche)']+=1; continue
        if v=='MIXITA': mixtes.append(g); src['melange -> cellule par cellule']+=1; continue
        if v is not None and len(v)==1: end_[g]=v; src['planche']+=1; continue
        src['modele']+=1
    np.save(f"{T}/cls_lab.npy", end_)
    np.save(f"{T}/groupes_mixtes.npy", np.array(mixtes,dtype=int))
    print("arbitrage :", dict(src))
    anc=np.load(f"{T}/cls_lab_avant_relecture_groupes.npy",allow_pickle=True)
    n=np.bincount(kl,minlength=K)
    d=[g for g in range(K) if end_[g]!=anc[g]]
    print("groups differing from the original labelling:",len(d)," cells:",int(n[d].sum()))
    return end_, mixtes

def cellules_mixtes(mixtes, out_path=f"{T}/exceptions_modele.txt"):
    """Cell-by-cell decoding of the mixed groups."""
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); M=np.load(f"{T}/meta_all.npy")
    kl=np.load(f"{T}/km_lab.npy")
    from features2 import feature_vector2
    m=pickle.load(open(f"{T}/modele3.pkl","rb"))
    sel=np.where(np.isin(kl, mixtes))[0]
    print("cells to decode one by one:",len(sel))
    ecrit=0
    with open(out_path,"w",encoding='utf-8') as f:
        f.write("# Cellules des groupes melanges, decodees une a une par le modele.\n")
        f.write("# Ce fichier a la priorite la plus basse : toute correction a la main l'emporte.\n")
        for a in range(0,len(sel),20000):
            b=sel[a:a+20000]
            X=feature_vector2(np.asarray(C[b]))
            P=m.predict_proba(X); cls=m.classes_
            j=P.argmax(1); p=P.max(1)
            for i,jj,pp in zip(b,j,p):
                if pp<0.55: continue          # too uncertain: we let the group decide
                ch=cls[jj]
                if ch==' ': continue
                pg,k,c=M[i]
                f.write(f"{int(pg)}\t{int(k)}\t{int(c)}\t{ch}\n"); ecrit+=1
    print("cells written:",ecrit)

if __name__=="__main__":
    end_,mix=run_step()
    cellules_mixtes(mix)
