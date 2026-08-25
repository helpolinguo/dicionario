# -*- coding: utf-8 -*-
"""Does the lattice of lines catch the top of the page properly?"""
import numpy as np, os, sys
from PIL import Image
RAC="/root/dicionario"; T=f"{RAC}/travail"
def une(pg):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    forme=tuple(z['shape']); lg=z['lignes']; pasv=float(z['pasv'])
    a=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape; ech=forme[0]/H
    b = a < (a.mean()-0.30*a.std())
    m=int(0.035*min(H,W)); b[:m]=False; b[-m:]=False; b[:,:m]=False; b[:,-m:]=False
    prof=b.sum(1)
    seuil=max(prof.max()*0.10, 6)
    w=np.where(prof>=seuil)[0]
    if not len(w) or not len(lg): return None
    haut_encre = w[0]*ech; bas_encre = w[-1]*ech
    y0=float(lg[0,1]); y1=float(lg[-1,1])
    # columns
    profc=b.sum(0); sc=max(profc.max()*0.06, 4)
    wc=np.where(profc>=sc)[0]
    gauche_encre = wc[0]*ech
    xg=float(z['xg']); col0=int(z['col0']); pash=float(z['pash'])
    x0 = xg + col0*pash
    return dict(pg=pg, lignes=len(lg), pasv=pasv,
                manque_haut=(y0-haut_encre)/pasv, manque_bas=(bas_encre-y1)/pasv,
                manque_gauche=(x0-gauche_encre)/pash)
if __name__=="__main__":
    a,b=int(sys.argv[1]), int(sys.argv[2])
    out=[]
    for pg in range(a,b):
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        try:
            r=une(pg)
            if r: out.append(r)
        except Exception as e: print("ECHEC",pg,e)
    import json; json.dump(out, open(f"{T}/diag_haut_{a}.json","w"))
    mh=np.array([r['manque_haut'] for r in out]); mg=np.array([r['manque_gauche'] for r in out])
    print("pages :",len(out))
    print("lignes manquantes en haut : moyenne %.2f, mediane %.2f, p90 %.2f, max %.2f"
          %(mh.mean(), np.median(mh), np.percentile(mh,90), mh.max()))
    print("  pages ou il manque >= 1 ligne en haut :", int((mh>=1).sum()), "(%.0f%%)"%(100*(mh>=1).mean()))
    print("  pages ou il manque >= 2 lignes en haut :", int((mh>=2).sum()))
    print("cellules manquantes a gauche : mediane %.2f, p90 %.2f, max %.2f"
          %(np.median(mg), np.percentile(mg,90), mg.max()))
    print("  pages ou il manque >= 1 colonne :", int((mg>=1).sum()))
