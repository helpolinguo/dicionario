# -*- coding: utf-8 -*-
"""Sheets for relabelling the least certain groups.

The classifier labels not cells but groups: an error of label on a group
propagates to all its members. Correcting the least certain groups therefore
corrects the whole book at a stroke, where re-reading the lines one by one
would cost a hundred times more.

One strip per group: the group's mean, then sixteen members drawn at random
(those nearest the centre at the head, the furthest at the tail, so that the
proofreader also sees what doubtful matter the group has picked up).
"""
import numpy as np, os
from PIL import Image, ImageDraw

T = "/root/dicionario/travail"
ZM   = 5     # magnification of the mean
ZS   = 3     # magnification of the members
NECH = 16    # members shown
PAR  = 11    # eleven groups: a sheet of 866 x 1400, no side beyond 1500

def _img(a, z):
    a = 255 - np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a).resize((a.shape[1]*z, a.shape[0]*z), Image.LANCZOS)

def planche(lot, sortie):
    """batch: list of (number, label, mean 22x12, list of members 22x12)."""
    hm, wm = 22*ZM, 12*ZM
    hs, ws = 22*ZS, 12*ZS
    marge, gap = 150, 16
    W = marge + wm + 24 + NECH*(ws+3) + 8
    H = 8 + len(lot)*(hm+gap)
    im = Image.new("RGB", (W, H), (255,255,255)); d = ImageDraw.Draw(im)
    for i,(num, eti, moy, membres) in enumerate(lot):
        y = 6 + i*(hm+gap)
        d.text((4, y+hm//2-14), f"{num}", fill=(200,0,0))
        d.text((4, y+hm//2+2),  f"[{eti}]", fill=(0,0,190))
        d.line([(marge-6, y-4), (W-4, y-4)], fill=(225,225,225))
        im.paste(_img(moy, ZM), (marge, y))
        d.line([(marge+wm+11, y), (marge+wm+11, y+hm)], fill=(180,180,180))
        x0 = marge+wm+24
        for j,c in enumerate(membres[:NECH]):
            im.paste(_img(c, ZS), (x0+j*(ws+3), y+(hm-hs)//2))
    im.save(sortie)
    return im.size

def preparer(groupes, rep=f"{T}/groupes", par=PAR):
    """groups: list of (number, label, mean, members)."""
    os.makedirs(rep, exist_ok=True)
    for f in os.listdir(rep):
        if f.startswith(("g","rez")) and f[-4:] in (".png",".txt"): os.remove(os.path.join(rep,f))
    lots=[groupes[i:i+par] for i in range(0,len(groupes),par)]
    for n,lot in enumerate(lots):
        planche(lot, f"{rep}/g{n:03d}.png")
        with open(f"{rep}/g{n:03d}.txt","w",encoding='utf-8') as f:
            for num,eti,_,_ in lot: f.write(f"{num}\t{eti}\n")
    return len(lots)
