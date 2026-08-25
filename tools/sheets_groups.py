# -*- coding: utf-8 -*-
"""Planches de reetiquetage des groupes peu surs.

Le classifieur etiquette non pas des cellules mais des groupes : une erreur
d'etiquette sur un groupe se propage a tous ses membres. Corriger les groupes
les moins surs corrige donc le livre entier d'un coup, la ou relire les lignes
une a une couterait cent fois plus.

Une bande par groupe : la moyenne du groupe, puis seize membres tires au
hasard (les plus proches du centre en tete, les plus lointains en queue, pour
que le relecteur voie aussi ce que le groupe ramasse de douteux).
"""
import numpy as np, os
from PIL import Image, ImageDraw

T = "/root/dicionario/travail"
ZM   = 5     # grossissement de la moyenne
ZS   = 3     # grossissement des membres
NECH = 16    # membres montres
PAR  = 11    # onze groupes : planche de 866 x 1400, aucun cote au-dela de 1500

def _img(a, z):
    a = 255 - np.clip(a, 0, 255).astype(np.uint8)
    return Image.fromarray(a).resize((a.shape[1]*z, a.shape[0]*z), Image.LANCZOS)

def planche(lot, sortie):
    """lot : liste de (numero, etiquette, moyenne 22x12, liste de membres 22x12)."""
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
    """groupes : liste de (numero, etiquette, moyenne, membres)."""
    os.makedirs(rep, exist_ok=True)
    for f in os.listdir(rep):
        if f.startswith(("g","rez")) and f[-4:] in (".png",".txt"): os.remove(os.path.join(rep,f))
    lots=[groupes[i:i+par] for i in range(0,len(groupes),par)]
    for n,lot in enumerate(lots):
        planche(lot, f"{rep}/g{n:03d}.png")
        with open(f"{rep}/g{n:03d}.txt","w",encoding='utf-8') as f:
            for num,eti,_,_ in lot: f.write(f"{num}\t{eti}\n")
    return len(lots)
