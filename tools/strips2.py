# -*- coding: utf-8 -*-
"""Targeted proofreading sheets, the version calibrated for reading by an agent.

The constraint: an image passed to a model is reduced to fit within about
1500 px. The previous version was 1988 x 4930: the reduction cancelled all
the magnification. We therefore size the sheet so that no side exceeds
~1400 px, at the cost of fewer headwords per sheet.
"""
import numpy as np, json, os, sys
from PIL import Image, ImageDraw
T = "/root/dicionario/travail"
NCEL = 30      # thirty cells: the headword and the start of the definition
ZOOM = 3       # 12x22 -> 36x66, legible without exceeding the useful width
PAR  = 16      # sixteen strips: a sheet of 1180 x 1270

_cache = {}
def cellules(pg):
    if pg not in _cache:
        z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
        _cache[pg] = (z['cells'], {int(k): i for i, k in enumerate(z['lignes'][:, 0])})
        if len(_cache) > 40: _cache.pop(next(iter(_cache)))
    return _cache[pg]

def planche(lot, sortie):
    h, w = 22, 12; tw, th = w*ZOOM, h*ZOOM
    marge = 74; gap = 14
    W = marge + NCEL*(tw+1) + 8
    H = 8 + len(lot)*(th+gap)
    im = Image.new("RGB", (W, H), (255, 255, 255)); d = ImageDraw.Draw(im)
    for i, (ident, pg, k, ved) in enumerate(lot):
        y = 6 + i*(th+gap)
        d.text((4, y+th//2-6), f"{ident}", fill=(200, 0, 0))
        try:
            C, idx = cellules(pg); r = idx.get(k)
        except Exception:
            r = None
        d.line([(marge-3, y-4), (W-4, y-4)], fill=(225, 225, 225))
        if r is None: continue
        band = C[r]
        for j in range(min(NCEL, band.shape[0])):
            g = Image.fromarray(255-np.clip(band[j], 0, 255).astype(np.uint8)).resize((tw, th), Image.LANCZOS)
            im.paste(g, (marge+j*(tw+1), y))
    im.save(sortie)
    return im.size

def preparer(entrees, rep=f"{T}/bandes2", par=PAR):
    os.makedirs(rep, exist_ok=True)
    for f in os.listdir(rep): os.remove(os.path.join(rep, f))
    lots = [entrees[i:i+par] for i in range(0, len(entrees), par)]
    for n, lot in enumerate(lots):
        planche([(e['id'], e['image'], e['ligno'], e['vedetto']) for e in lot],
                f"{rep}/b{n:03d}.png")
        with open(f"{rep}/b{n:03d}.txt", "w", encoding='utf-8') as f:
            for e in lot: f.write(f"{e['id']}\t{e['vedetto']}\n")
    return len(lots)
