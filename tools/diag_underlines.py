# -*- coding: utf-8 -*-
"""Bande de scan autour de quelques lignes, avec les filets detectes marques.
Sert a voir ou l'encre du filet se trouve reellement."""
import numpy as np, sys, pickle
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image, ImageDraw
T="/root/dicionario/travail"; RAC="/root/dicionario"

def bande(pg, k0, k1, Z=3, sortie=None):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=dict((int(k),float(y)) for k,y in z['lignes'])
    pasv=float(z['pasv']); pash=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    sou=pickle.loads(z['sou'].item())
    r=z['nues'] if 'nues' in z else None
    img=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert("L"),dtype=np.float32)/255.0
    H,W=z['shape']
    ech=img.shape[0]/float(H)
    y0=int((lg[k0]-0.7*pasv)*ech); y1=int((lg[k1]+0.9*pasv)*ech)
    crop=img[y0:y1]
    im=Image.fromarray((np.clip(crop,0,1)*255).astype(np.uint8)).convert("RGB")
    im=im.resize((int(im.width*Z/ech), int(im.height*Z/ech)), Image.LANCZOS)
    d=ImageDraw.Draw(im)
    for k in range(k0,k1+1):
        if k not in lg: continue
        yy=(lg[k]-y0/ech)*Z
        d.line([(0,yy),(im.width,yy)], fill=(0,160,255), width=1)
        d.text((2,yy-11), "k=%d"%k, fill=(0,120,220))
        if k in sou:
            rows,pl,tot=sou[k]
            for rr in (rows or []):
                yr=(rr-y0/ech)*Z
                d.line([(0,yr),(im.width,yr)], fill=(255,200,0), width=1)
            for a,b in pl:
                xa=(xg+(a+c0)*pash-0)*Z; xb=(xg+(b+1+c0)*pash)*Z
                yr=(lg[k]+0.62*pasv-y0/ech)*Z
                d.rectangle([xa,yr-2,xb,yr+2], outline=(255,0,0))
    p=sortie or f"{T}/sou-p{pg:03d}-{k0}.png"
    im.save(p); print(p, im.size)

if __name__=="__main__":
    bande(33,16,18); bande(25,26,28); bande(10,51,53)
