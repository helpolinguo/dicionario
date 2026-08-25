# -*- coding: utf-8 -*-
"""Gives back the line ends the block was cutting off, without re-cutting the book.

The block of text is bounded by the columns inked on at least three lines:
994 characters, at the end of 728 lines, fell outside. Recovering them by
widening the block meant re-cutting every page -- which lost headwords on a
hundred and forty-five of them.

We therefore recover them otherwise: the page is re-cut in memory with the
extended block, the cells that overflow are attached to the group whose
centre is nearest, and they are added to the text as plain corrections in the
columns that follow the block. The recorded cutting does not move: no
correction already made is invalidated.
"""
import sys, os, json
import numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
import cells
from features2 import feature_vector2
ROOT=_ROOT; T=f"{ROOT}/work"

def one_(pg, Q, tab, bleed_thresholds=True):
    z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    ncol=z['occ'].shape[1]; col0=int(z['col0'])
    keys_=set(int(k) for k,_ in z['lignes'])
    cells.EXTEND=False; cells.EXTEND_RIGHT=True
    d=cells.extract(f"{ROOT}/scan/p-{pg:03d}.jpg")
    c0=int(d['col0']); lg=np.array(d['lignes'])
    if c0!=col0: return None, "origine des colonnes deplacee"
    if set(int(k) for k in lg[:,0]) != keys_: return None, "lignes differentes"
    start_=ncol
    occ=d['occ']
    if occ.shape[1] <= start_: return [], None
    ii,jj=np.where(occ[:, start_:])
    if not len(ii): return [], None
    jj=jj+start_
    A=(np.clip(d['nues'][ii,jj],0,1)*255.0).round().astype(np.uint8)
    P=A.astype(np.float32)/255.
    tot=P.sum((1,2))
    edge=(P[:,:,:2].sum((1,2))+P[:,:,-2:].sum((1,2)))/(tot+1e-6)
    top=P[:,:4,:].sum((1,2))/(tot+1e-6); bottom=P[:,18:,:].sum((1,2))/(tot+1e-6)
    smudge=((edge>0.55)|((tot<12)&(edge>0.25))|(top>0.80)|(bottom>0.85))
    X=feature_vector2(A); X=X/np.maximum(np.linalg.norm(X,axis=1,keepdims=True),1e-6)
    g=(X@Q.T).argmax(1)
    out=[]
    for i in range(len(ii)):
        if smudge[i]: continue
        ch=str(tab[g[i]])
        if ch==' ' or len(ch)!=1: continue
        out.append((pg, int(lg[ii[i],0]), int(jj[i]), ch))
    return out, None

if __name__=="__main__":
    a,b=int(sys.argv[1]), int(sys.argv[2])
    Q=np.load(f"{T}/km_centres2.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    corr_=[]; refused=[]
    for pg in range(a,b):
        if not os.path.exists(f"{T}/cells/p-{pg:03d}.npz"): continue
        if pg in (0,1,3,7,87,111,577): continue
        try:
            r,err=one_(pg,Q,tab)
            if err: refused.append((pg,err))
            else: corr_+=r
        except Exception as e: refused.append((pg,str(e)))
    json.dump(dict(cor=corr_, refus=refused), open(f"{T}/ends_corr_{a}.json","w"))
    print(f"{a}-{b} : {len(corr_)} characters given back ; {len(refused)} pages refused")
