# -*- coding: utf-8 -*-
"""Recalcule les filets de soulignement sans redecouper les pages.

On rejoue exactement la sequence de extraire() jusqu'a soulignements() —
analyser(), raffiner_pas(), soulignements() — puis on decale des colonnes par
le col0 deja stocke. Sans changement de regle, le resultat doit etre
identique a ce qui est dans le npz : c'est le controle de non-regression.
"""
import numpy as np, sys, pickle, os, re
sys.path.insert(0,'/root/dicionario/outils')
import cells as C
T="/root/dicionario/travail"; RAC="/root/dicionario"

def filets(pg, **kw):
    """Filets d'une page, sur la geometrie DEJA STOCKEE.

    On ne recalcule surtout pas le pas et la phase du lattis. raffiner_pas()
    ne rend pas exactement la meme origine d'une fois sur l'autre, et une
    cellule n'est retenue que si le filet la couvre a 60 % : au bord gauche
    d'une vedette, le filet tombe pile sur ce seuil. Un xg different d'un
    demi-pixel faisait donc passer la premiere cellule de 0 a 1 — et
    generate.py, qui refuse un filet commencant au milieu d'un mot, jetait
    alors le soulignement entier de la vedette. Huit vedettes d'affilee y sont
    passees a la page 155.

    Seule l'image rectifiee vient de analyser() ; les lignes, le pas et
    l'origine viennent du npz, comme au premier decoupage.
    """
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    d = C.analyser(f"{RAC}/scan/p-{pg:03d}.jpg")
    r=d['norm']
    pasv=float(z['pasv']); pash=float(z['pash']); xg=float(z['xg']); c0=int(z['col0'])
    ncol=int(np.floor((r.shape[1]-xg)/pash))
    sou = C.soulignements(r, z['lignes'], pasv, pash, xg, ncol, **kw)
    return {k:(yy,[(a-c0,b-c0) for a,b in pl],t) for k,(yy,pl,t) in sou.items()}

if __name__=="__main__":
    for pg in (25,33):
        neuf=filets(pg)
        z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
        anc=pickle.loads(z['sou'].item())
        ka=set(k for k,v in anc.items() if v[1]); kn=set(k for k,v in neuf.items() if v[1])
        egal=all(sorted(anc[k][1])==sorted(neuf[k][1]) for k in ka|kn if k in anc and k in neuf)
        print("p%03d : lignes avec filet anc=%d neuf=%d  identiques=%s"%(pg,len(ka),len(kn),egal and ka==kn))

def tous(sortie=f"{T}/filets.pkl", debut=0, fin=None):
    """Recalcule les filets de toutes les pages et les depose a part.

    On n'ecrit pas dans le corpus de cellules : il pese 295 Mo et une erreur
    de format y a deja coute 144 pages. Le fichier produit ici est une couche
    de correction, lue par generate.py apres le releve a l'oeil et avant la
    detection d'origine.
    """
    import glob
    pages=sorted(int(re.search(r'p-(\d+)',f).group(1))
                 for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages=[p for p in pages if p>=debut and (fin is None or p<fin)]
    out={}
    for i,pg in enumerate(pages):
        try:
            out[pg]=filets(pg)
        except Exception as e:
            print("ECHEC p%03d : %s"%(pg,e), flush=True); continue
        if i%25==0: print("  %d/%d (p%03d)"%(i,len(pages),pg), flush=True)
    with open(sortie,"wb") as f: pickle.dump(out,f)
    print("ecrit %s : %d pages"%(sortie,len(out)))
    return out
