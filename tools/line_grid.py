# -*- coding: utf-8 -*-
"""A strip of scan of one line, with the grid of cells and the column
indices: to read off the scan which cell carries which character."""
import numpy as np, sys
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from PIL import Image, ImageDraw
T=_ROOT + "/work"; ROOT=_ROOT

def band(pg, k, c0v=0, c1v=None, Z=6, out_path=None):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=dict((int(a),float(b)) for a,b in z['lignes'])
    vstep=float(z['pasv']); hstep=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    ncol=z['occ'].shape[1]
    if c1v is None: c1v=ncol
    img=np.asarray(Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert("L"),dtype=np.float32)/255.
    H,W=z['shape']; scale=img.shape[0]/float(H)
    ya=int((lg[k]-0.95*vstep)*scale); yb=int((lg[k]+0.45*vstep)*scale)
    xa=(xg+(c0v+c0)*hstep)*scale; xb=(xg+(c1v+c0)*hstep)*scale
    c=img[ya:yb, int(xa):int(xb)]
    im=Image.fromarray((np.clip(c,0,1)*255).astype(np.uint8)).convert("RGB")
    im=im.resize((int(c.shape[1]*Z), int(c.shape[0]*Z)), Image.LANCZOS)
    pl=Image.new('RGB',(im.width, im.height+22),(255,255,255))
    pl.paste(im,(0,22)); d=ImageDraw.Draw(pl)
    for j in range(c0v, c1v+1):
        x=((xg+(j+c0)*hstep)*scale - xa)*Z
        d.line([(x,22),(x,pl.height)], fill=(255,120,120))
        if j%2==0: d.text((x+1,4), str(j%100), fill=(200,0,0))
    p=out_path or f"{T}/l-p{pg:03d}-k{k}.png"
    pl.save(p); print(p, pl.size)

if __name__=="__main__":
    band(474,50,0,32); band(474,53,0,32)
