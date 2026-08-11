# -*- coding: utf-8 -*-
"""Releve des « + » en exposant devant les vedettes non officielles.

Le signe est frappe une demi-hauteur au-dessus de la ligne. La cellule qui le
porte n'est pas marquee occupee — c'est pourquoi un releve fonde sur occ ne le
voit pas. On mesure donc l'encre directement dans le scan, dans le haut de la
cellule qui precede la vedette.
"""
import sys, numpy as np, glob, re
sys.path.insert(0,'/root/dicionario/outils')
from decoder import charger
from generer import lignes_page
from PIL import Image
T="/root/dicionario/travail"; RAC="/root/dicionario"

def releve(seuil=0.20):
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    trouves=[]
    for f in sorted(glob.glob(f"{T}/cellules/p-*.npz")):
        pg=int(re.search(r'p-(\d+)',f).group(1))
        z=np.load(f, allow_pickle=True)
        try: lignes,ncol=lignes_page(pg,lab,M,tab)
        except Exception: continue
        cands=[(k,"".join(c)) for k,c,pl in lignes
               if len("".join(c))>3 and "".join(c)[0]==" " and "".join(c)[1] not in " "]
        if not cands: continue
        lg=dict((int(a),float(b)) for a,b in z['lignes'])
        pasv=float(z['pasv']); pash=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
        img=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert("L"),dtype=np.float32)/255.
        H,W=z['shape']; ech=img.shape[0]/float(H)
        for k,t in cands:
            if k not in lg: continue
            # haut de la cellule 0 : de -1,0 a -0,35 interligne sous la ligne de base
            ya=int((lg[k]-1.00*pasv)*ech); yb=int((lg[k]-0.30*pasv)*ech)
            xa=int((xg+(0+c0)*pash)*ech); xb=int((xg+(1+c0)*pash)*ech)
            if yb<=ya or xb<=xa or yb>img.shape[0]: continue
            enc=1.0-img[ya:yb, xa:xb]
            if enc.max()>0.55 and enc.mean()>seuil*0.5:
                trouves.append((pg,k,round(float(enc.mean()),3),t[1:18].rstrip()))
    return trouves

if __name__=="__main__":
    t=releve()
    print("vedettes precedees d'un signe encre en colonne 0 :",len(t))
    for pg,k,e,mot in t: print("   p%03d k=%-3d encre %.3f  %s"%(pg,k,e,mot))
