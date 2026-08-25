# -*- coding: utf-8 -*-
"""Targeted proofreading sheets: one strip of image per reported headword.

Instead of having whole pages re-read, we show only what is at issue: the
headword's line, over its first thirty cells, with its number. Forty
headwords fit on one sheet.
"""
import numpy as np, json, os, sys
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image, ImageDraw
T="/root/dicionario/travail"
NCEL=30; ZOOM=5; PAR=40

_cache={}
def cells_of(pg):
    if pg not in _cache:
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
        _cache[pg]=(z['cells'], {int(k):i for i,k in enumerate(z['lignes'][:,0])})
        if len(_cache)>40: _cache.pop(next(iter(_cache)))
    return _cache[pg]

def sheet_(batch, out_path):
    """batch: list of (identifier, image, line, proposed_headword)."""
    h,w=22,12; tw,th=w*ZOOM,h*ZOOM
    margin=118
    W=margin+NCEL*(tw+2)+10; H=10+len(batch)*(th+13)
    im=Image.new("RGB",(W,H),(255,255,255)); d=ImageDraw.Draw(im)
    for i,(ident,pg,k,hw) in enumerate(batch):
        y=6+i*(th+13)
        d.text((4,y+th//2-6), f"{ident}", fill=(190,0,0))
        try:
            C,idx=cells_of(pg); r=idx.get(k)
        except Exception: r=None
        if r is None: continue
        band=C[r]
        for j in range(min(NCEL, band.shape[0])):
            x=margin+j*(tw+2)
            g=Image.fromarray(255-np.clip(band[j],0,255).astype(np.uint8)).resize((tw,th),Image.LANCZOS)
            im.paste(g,(x,y))
        d.line([(margin-4,y-3),(W-4,y-3)], fill=(232,232,232))
    im.save(out_path)
    return im.size

def preparer(entries, rep=f"{T}/bandes", per=PAR):
    os.makedirs(rep, exist_ok=True)
    batches=[entries[i:i+per] for i in range(0,len(entries),per)]
    for n,batch in enumerate(batches):
        sheet_([(e['id'], e['image'], e['ligno'], e['vedetto']) for e in batch],
                f"{rep}/bande{n:03d}.png")
        with open(f"{rep}/bande{n:03d}.txt","w",encoding='utf-8') as f:
            for e in batch: f.write(f"{e['id']}\t{e['vedetto']}\n")
    return len(batches)
