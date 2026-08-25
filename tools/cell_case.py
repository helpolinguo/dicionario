# -*- coding: utf-8 -*-
"""The decision of case, cell by cell, by comparison with the line itself.

Two attempts failed before this one, and they say why this one holds.

1. The top of the ink, an absolute threshold. Disastrous: a cell's window
   bites into its neighbours, and one speck is enough to make an « a » pass
   for an « A ».
2. The top of the connected component carrying the body of the letter, an
   absolute threshold. Still losing. On finally looking at the faulty cells,
   the reason leaps out: on some pages the lower case rises as high, in rows
   of the screen, as the capitals of other pages. The scan's scale is not
   constant; an absolute threshold therefore measures nothing.

Hence the rule adopted: we do not compare a letter with a threshold, we
compare it with the letters of its own line. Every line of this dictionary
contains ascenders -- « b d f h k l t » -- that rise to the height of the
capitals, and x-height letters -- « a c e m n o r s u v w x z » -- that stop
halfway. Those two cues give the line's scale. An x-height letter that rises
towards the ascenders is a capital.
"""
import numpy as np, sys
from scipy.ndimage import label as cclabel
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"
XH  = "acemnorsuvwxz"     # x-height: it is on these that the doubt falls
STEM = "bdfhklt"         # ascenders: they give the height of the capitals
MINI = 4                  # minimum cues of each kind on the line
PART = 0.35               # fraction of the way from ascender to x-height
_ST = np.ones((3,3),int)

def letter_top(A):
    """The top of the connected component carrying the body of the letter."""
    B=(A>60); n=len(A); sum_=np.full(n,np.nan)
    for i in range(n):
        b=B[i]
        if b.sum()<4: continue
        L,k=cclabel(b, structure=_ST)
        if k==0: continue
        best=0; sc=-1
        for j in range(1,k+1):
            s=int((L[8:15]==j).sum())
            if s>sc: sc=s; best=j
        if sc<=0: continue
        w=np.where((L==best).any(1))[0]
        if len(w): sum_[i]=w[0]
    return sum_

def run_step(out_path=f"{T}/exceptions_casse.txt"):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); M=np.load(f"{T}/meta_all.npy")
    kl=np.load(f"{T}/km_lab.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    from decode import smudges
    bv=smudges()
    char_=np.array([str(tab[k]) for k in range(len(tab))], dtype=object)
    # grouping by line
    key_ = M[:,0].astype(np.int64)*10000 + M[:,1].astype(np.int64)
    o=np.argsort(key_, kind='stable'); bounds=np.flatnonzero(np.r_[True, np.diff(key_[o])!=0, True])
    written=0; lines=0
    with open(out_path,"w",encoding='utf-8') as f:
        f.write("# Casse tranchee par comparaison aux hampes de la meme ligne.\n")
        f.write("# Priorite basse : toute correction a la main l'emporte.\n")
        for a,b in zip(bounds[:-1], bounds[1:]):
            g=o[a:b]
            g=g[~bv[g]]
            if len(g)<8: continue
            c=char_[kl[g]]
            mx=np.array([x in XH for x in c]); mh=np.array([x in STEM for x in c])
            if mx.sum()<MINI or mh.sum()<MINI: continue
            sum_=letter_top(np.asarray(C[np.sort(g)]).astype(np.float32))
            sum_=sum_[np.argsort(np.argsort(g))]      # put back into the order of g
            sx=np.nanmedian(sum_[mx]); sh=np.nanmedian(sum_[mh])
            if np.isnan(sx) or np.isnan(sh) or sx-sh < 1.5: continue
            threshold = sh + PART*(sx-sh)
            lines+=1
            for i in np.where(mx)[0]:
                if np.isnan(sum_[i]) or sum_[i]>threshold: continue
                pg,k,cc=M[g[i]]
                f.write(f"{int(pg)}\t{int(k)}\t{int(cc)}\t{c[i].upper()}\n"); written+=1
    print("lines calibrated:",lines," cells raised to a capital:",written)

if __name__=="__main__": run_step()
