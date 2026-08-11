# -*- coding: utf-8 -*-
"""Rend les fins de ligne que le bloc coupait, sans redecouper le livre.

Le bloc de texte est cerne par les colonnes encrees sur au moins trois lignes :
994 caracteres, en bout de 728 lignes, tombaient dehors. Les recuperer en
elargissant le bloc obligeait a redecouper toutes les pages — ce qui faisait
perdre des vedettes a cent quarante-cinq d'entre elles.

On les recupere donc autrement : la page est recoupee en memoire avec le bloc
etendu, les cellules qui debordent sont rattachees au groupe dont le centre est
le plus proche, et elles sont ajoutees au texte comme de simples corrections
aux colonnes qui suivent le bloc. Le decoupage enregistre, lui, ne bouge pas :
aucune correction deja faite n'est invalidee.
"""
import sys, os, json
import numpy as np
sys.path.insert(0,'/root/dicionario/outils')
import cellules
from traits2 import traits2
RAC="/root/dicionario"; T=f"{RAC}/travail"

def une(pg, Q, tab, bav_seuils=True):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    ncol=z['occ'].shape[1]; col0=int(z['col0'])
    cles=set(int(k) for k,_ in z['lignes'])
    cellules.ETENDRE=False; cellules.ETENDRE_D=True
    d=cellules.extraire(f"{RAC}/scan/p-{pg:03d}.jpg")
    c0=int(d['col0']); lg=np.array(d['lignes'])
    if c0!=col0: return None, "origine des colonnes deplacee"
    if set(int(k) for k in lg[:,0]) != cles: return None, "lignes differentes"
    debut=ncol
    occ=d['occ']
    if occ.shape[1] <= debut: return [], None
    ii,jj=np.where(occ[:, debut:])
    if not len(ii): return [], None
    jj=jj+debut
    A=(np.clip(d['nues'][ii,jj],0,1)*255.0).round().astype(np.uint8)
    P=A.astype(np.float32)/255.
    tot=P.sum((1,2))
    bord=(P[:,:,:2].sum((1,2))+P[:,:,-2:].sum((1,2)))/(tot+1e-6)
    haut=P[:,:4,:].sum((1,2))/(tot+1e-6); bas=P[:,18:,:].sum((1,2))/(tot+1e-6)
    bav=((bord>0.55)|((tot<12)&(bord>0.25))|(haut>0.80)|(bas>0.85))
    X=traits2(A); X=X/np.maximum(np.linalg.norm(X,axis=1,keepdims=True),1e-6)
    g=(X@Q.T).argmax(1)
    out=[]
    for i in range(len(ii)):
        if bav[i]: continue
        ch=str(tab[g[i]])
        if ch==' ' or len(ch)!=1: continue
        out.append((pg, int(lg[ii[i],0]), int(jj[i]), ch))
    return out, None

if __name__=="__main__":
    a,b=int(sys.argv[1]), int(sys.argv[2])
    Q=np.load(f"{T}/km_centres2.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    cor=[]; refus=[]
    for pg in range(a,b):
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        if pg in (0,1,3,7,87,111,577): continue
        try:
            r,err=une(pg,Q,tab)
            if err: refus.append((pg,err))
            else: cor+=r
        except Exception as e: refus.append((pg,str(e)))
    json.dump(dict(cor=cor, refus=refus), open(f"{T}/fins_cor_{a}.json","w"))
    print(f"{a}-{b} : {len(cor)} caracteres rendus ; {len(refus)} pages refusees")
