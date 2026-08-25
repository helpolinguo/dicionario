# -*- coding: utf-8 -*-
"""Planches de relecture ciblees : une bande d'image par vedette signalee.

Au lieu de faire relire des pages entieres, on ne montre que ce qui est en
cause : la ligne de la vedette, sur ses trente premieres cellules, avec son
numero. Quarante vedettes tiennent sur une planche.
"""
import numpy as np, json, os, sys
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image, ImageDraw
T="/root/dicionario/travail"
NCEL=30; ZOOM=5; PAR=40

_cache={}
def cellules(pg):
    if pg not in _cache:
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
        _cache[pg]=(z['cells'], {int(k):i for i,k in enumerate(z['lignes'][:,0])})
        if len(_cache)>40: _cache.pop(next(iter(_cache)))
    return _cache[pg]

def planche(lot, sortie):
    """lot : liste de (identifiant, image, ligne, vedette_proposee)."""
    h,w=22,12; tw,th=w*ZOOM,h*ZOOM
    marge=118
    W=marge+NCEL*(tw+2)+10; H=10+len(lot)*(th+13)
    im=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(im)
    for i,(ident,pg,k,ved) in enumerate(lot):
        y=6+i*(th+13)
        d.text((4,y+th//2-6), f"{ident}", fill=(190,0,0))
        try:
            C,idx=cellules(pg); r=idx.get(k)
        except Exception: r=None
        if r is None: continue
        band=C[r]
        for j in range(min(NCEL, band.shape[0])):
            x=marge+j*(tw+2)
            g=Image.fromarray(255-np.clip(band[j],0,255).astype(np.uint8)).resize((tw,th),Image.LANCZOS)
            im.paste(g,(x,y))
        d.line([(marge-4,y-3),(W-4,y-3)], fill=(232,232,232))
    im.save(sortie)
    return im.size

def preparer(entrees, rep=f"{T}/bandes", par=PAR):
    os.makedirs(rep, exist_ok=True)
    lots=[entrees[i:i+par] for i in range(0,len(entrees),par)]
    for n,lot in enumerate(lots):
        planche([(e['id'], e['image'], e['ligno'], e['vedetto']) for e in lot],
                f"{rep}/bande{n:03d}.png")
        with open(f"{rep}/bande{n:03d}.txt","w",encoding='utf-8') as f:
            for e in lot: f.write(f"{e['id']}\t{e['vedetto']}\n")
    return len(lots)
