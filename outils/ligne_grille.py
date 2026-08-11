# -*- coding: utf-8 -*-
"""Bande de scan d'une ligne, avec la grille de cellules et les indices de
colonne : pour lire au scan quelle cellule porte quel caractere."""
import numpy as np, sys
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image, ImageDraw
T="/root/dicionario/travail"; RAC="/root/dicionario"

def bande(pg, k, c0v=0, c1v=None, Z=6, sortie=None):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=dict((int(a),float(b)) for a,b in z['lignes'])
    pasv=float(z['pasv']); pash=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    ncol=z['occ'].shape[1]
    if c1v is None: c1v=ncol
    img=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert("L"),dtype=np.float32)/255.
    H,W=z['shape']; ech=img.shape[0]/float(H)
    ya=int((lg[k]-0.95*pasv)*ech); yb=int((lg[k]+0.45*pasv)*ech)
    xa=(xg+(c0v+c0)*pash)*ech; xb=(xg+(c1v+c0)*pash)*ech
    c=img[ya:yb, int(xa):int(xb)]
    im=Image.fromarray((np.clip(c,0,1)*255).astype(np.uint8)).convert("RGB")
    im=im.resize((int(c.shape[1]*Z), int(c.shape[0]*Z)), Image.LANCZOS)
    pl=Image.new('RGB',(im.width, im.height+22),(255,255,255))
    pl.paste(im,(0,22)); d=ImageDraw.Draw(pl)
    for j in range(c0v, c1v+1):
        x=((xg+(j+c0)*pash)*ech - xa)*Z
        d.line([(x,22),(x,pl.height)], fill=(255,120,120))
        if j%2==0: d.text((x+1,4), str(j%100), fill=(200,0,0))
    p=sortie or f"{T}/l-p{pg:03d}-k{k}.png"
    pl.save(p); print(p, pl.size)

if __name__=="__main__":
    bande(474,50,0,32); bande(474,53,0,32)
