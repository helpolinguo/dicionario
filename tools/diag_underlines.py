# -*- coding: utf-8 -*-
"""A strip of scan around a few lines, with the detected rules marked.
Serves to see where the rule's ink actually is."""
import numpy as np, sys, pickle
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image, ImageDraw
T="/root/dicionario/travail"; ROOT="/root/dicionario"

def band(pg, k0, k1, Z=3, out_path=None):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=dict((int(k),float(y)) for k,y in z['lignes'])
    vstep=float(z['pasv']); hstep=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    underline=pickle.loads(z['sou'].item())
    r=z['nues'] if 'nues' in z else None
    img=np.asarray(Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert("L"),dtype=np.float32)/255.0
    H,W=z['shape']
    scale=img.shape[0]/float(H)
    y0=int((lg[k0]-0.7*vstep)*scale); y1=int((lg[k1]+0.9*vstep)*scale)
    crop=img[y0:y1]
    im=Image.fromarray((np.clip(crop,0,1)*255).astype(np.uint8)).convert("RGB")
    im=im.resize((int(im.width*Z/scale), int(im.height*Z/scale)), Image.LANCZOS)
    d=ImageDraw.Draw(im)
    for k in range(k0,k1+1):
        if k not in lg: continue
        yy=(lg[k]-y0/scale)*Z
        d.line([(0,yy),(im.width,yy)], fill=(0,160,255), width=1)
        d.text((2,yy-11), "k=%d"%k, fill=(0,120,220))
        if k in underline:
            rows,pl,tot=underline[k]
            for rr in (rows or []):
                yr=(rr-y0/scale)*Z
                d.line([(0,yr),(im.width,yr)], fill=(255,200,0), width=1)
            for a,b in pl:
                xa=(xg+(a+c0)*hstep-0)*Z; xb=(xg+(b+1+c0)*hstep)*Z
                yr=(lg[k]+0.62*vstep-y0/scale)*Z
                d.rectangle([xa,yr-2,xb,yr+2], outline=(255,0,0))
    p=out_path or f"{T}/sou-p{pg:03d}-{k0}.png"
    im.save(p); print(p, im.size)

if __name__=="__main__":
    band(33,16,18); band(25,26,28); band(10,51,53)
