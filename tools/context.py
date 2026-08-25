"""Shows occurrences of a group in the line they came from."""
import numpy as np
from PIL import Image, ImageDraw
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"
_cache={}
def page(pg):
    if pg not in _cache:
        _cache[pg]=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    return _cache[pg]
def context(groups, lab, M, k, n=8, before_=10, after_=10, zoom=4, seed=0):
    idx=np.where(lab==k)[0]
    rng=np.random.default_rng(seed)
    if len(idx)>n: idx=rng.choice(idx,n,replace=False)
    strips=[]
    for i in idx:
        pg,kk,c=M[i]
        z=page(int(pg)); cells=z['cells']; lg=z['lignes']
        r=[t for t,(k2,_) in enumerate(lg) if k2==kk]
        if not r: continue
        r=r[0]
        a=max(int(c)-before_,0); b=min(int(c)+after_+1, cells.shape[1])
        strips.append((cells[r,a:b], int(c)-a, f"p{int(pg)} l{int(kk)} c{int(c)}"))
    if not strips: return None
    h,w=22,12; tw,th=w*zoom,h*zoom
    W=110+max(b[0].shape[0] for b in strips)*tw+8
    H=6+len(strips)*(th+8)
    im=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(im)
    for i,(band,pos,txt) in enumerate(strips):
        y=4+i*(th+8)
        d.text((3,y+th//2-6), txt, fill=(120,120,120))
        for j in range(band.shape[0]):
            x=110+j*tw
            g=Image.fromarray(255-np.clip(band[j],0,255).astype(np.uint8)).resize((tw,th),Image.LANCZOS)
            im.paste(g,(x,y))
            if j==pos: d.rectangle([x,y,x+tw-1,y+th-1], outline=(220,0,0))
    return im
