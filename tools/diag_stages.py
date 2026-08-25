# -*- coding: utf-8 -*-
"""Where the letters die: scan / binarisation / after despeckling 1 /
after despeckling 2. One row per stage, to read by eye the exact moment
a stroke disappears."""
import numpy as np, sys, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from cover import binarise_stroke, OVERSAMPLE
from repair_cover import apply_
from scipy.ndimage import label as _lab, binary_dilation as _dil, find_objects
from PIL import Image, ImageDraw
ROOT=_ROOT
BOXES=[(21,138,264,394),(188,288,218,359),(379,458,187,331),(546,638,175,323),
        (720,801,188,330),(877,974,218,358),(1034,1136,285,394)]

def stages():
    c=f"{ROOT}/work/cover/stages.npz"
    if os.path.exists(c):
        z=np.load(c); return z['b'],z['d1'],z['d2']
    n=np.load(f"{ROOT}/work/cover/levels.npy")
    b=apply_(binarise_stroke(n))
    d1=b.copy()
    R=22*OVERSAMPLE
    am,na=_lab(_dil(d1,np.ones((R,R),bool)),np.ones((3,3),int))
    ink_=np.bincount(am[d1].ravel(),minlength=na+1)
    du=np.where(ink_<1500)[0]; du=du[du>0]
    d1 &= ~(np.isin(am,du)&d1)
    d2=d1.copy()
    LH,LV,AREA,INK,THICK,FAR=12,6,900,1500,900,12
    mp=np.zeros(d2.shape,bool)
    for (x0,x1,y0,y1) in BOXES:
        m=8; mp[(max(y0-m,0))*OVERSAMPLE:(y1+m)*OVERSAMPLE,(max(x0-m,0))*OVERSAMPLE:(x1+m)*OVERSAMPLE]=True
    T=d2&~mp
    d=_dil(T,np.ones((1,LH*OVERSAMPLE),bool)); d=_dil(d,np.ones((LV*OVERSAMPLE,1),bool))
    am,nb=_lab(d,np.ones((3,3),int)); ink_=np.bincount(am[T].ravel(),minlength=nb+1)
    l,n2=_lab(T,np.ones((3,3),int)); ob=find_objects(l)
    ai=np.array([int((l[ob[i]]==i+1).sum()) for i in range(n2)])
    bb=np.array([(o[0].start,o[0].stop,o[1].start,o[1].stop) for o in ob])
    g=np.nonzero(ai>=THICK)[0]; Y0,Y1,X0,X1=bb[:,0],bb[:,1],bb[:,2],bb[:,3]
    for i,o in enumerate(ob):
        if ai[i]>=AREA: continue
        ys,xs=np.nonzero(l[o]==i+1)
        if ink_[am[o][ys[0],xs[0]]]>=INK: continue
        if len(g):
            dy=np.maximum(0,np.maximum(Y0[i]-Y1[g],Y0[g]-Y1[i]))
            dx=np.maximum(0,np.maximum(X0[i]-X1[g],X0[g]-X1[i]))
            if np.hypot(dy,dx).min()<=FAR*OVERSAMPLE: continue
        d2[o] &= ~(l[o]==i+1)
    np.savez_compressed(c,b=b,d1=d1,d2=d2)
    return b,d1,d2

def sheet_(name_,x0,x1,y0,y1,Z=5):
    n=np.load(f"{ROOT}/work/cover/levels.npy")
    b,d1,d2=stages()
    W=(x1-x0)*Z; H=(y1-y0)*Z
    views=[("SCAN", np.clip(1-n[y0:y1,x0:x1],0,1)*255)]
    for t,A in (("BINARISATION",b),("APRES DEPOUSS. 1",d1),("APRES DEPOUSS. 2",d2)):
        views.append((t, (~A[y0*OVERSAMPLE:y1*OVERSAMPLE, x0*OVERSAMPLE:x1*OVERSAMPLE]*255).astype(np.uint8)))
    pl=Image.new('L',(W,(H+22)*len(views)),255); d=ImageDraw.Draw(pl)
    for i,(t,a) in enumerate(views):
        im=Image.fromarray(a.astype(np.uint8)).resize((W,H),Image.LANCZOS)
        d.text((4,i*(H+22)+4),t,fill=0); pl.paste(im,(0,i*(H+22)+20))
    os.makedirs(f"{ROOT}/work/audit",exist_ok=True)
    pl.save(f"{ROOT}/work/audit/stages-{name_}.png"); print(name_,pl.size)

if __name__=="__main__":
    sheet_("lalande",546,800,415,505,Z=6)
