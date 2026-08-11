"""Consolidation des initiales de vedette par l'ordre alphabetique du livre.

Le dictionnaire est alphabetique : sur une page donnee, les vedettes commencent
presque toutes par la meme lettre. Or c'est justement la que le decodage se
trompe le plus (20 % de fautes sur les trois premieres colonnes, contre 2 %
ailleurs), parce que l'initiale porte un soulignement souvent double.

On releve donc, page par page, la lettre majoritaire des initiales de vedette,
et on l'impose aux cellules qui la contredisent. Ce n'est pas une correction du
tapuscrit : c'est la levee d'une ambiguite de lecture par une propriete
structurelle du livre. Chaque intervention est journalisee.
"""
import numpy as np, pickle, collections, sys
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"

def vedettes(pg):
    """Lignes de vedette : colonne 0 encree et filet commencant a la colonne 0."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    occ=z['occ']; lg=z['lignes']; sou=pickle.loads(z['sou'].item())
    out=[]
    for i,k in enumerate(lg[:,0]):
        k=int(k)
        if not occ[i,0]: continue
        r=sou.get(k)
        if not r: continue
        plages=r[1]
        if any(a<=0<=b for a,b in plages): out.append((k,i))
    return out

def consolider(lab, M, tab, pages=None, seuil=0.6, mini=3):
    """Retourne (nouvelle table, journal). La table n'est pas modifiee en place."""
    import glob, os
    if pages is None:
        pages=[int(os.path.basename(p)[2:5]) for p in sorted(glob.glob(f"{T}/cellules/*.npz"))]
    tab=np.array(tab, dtype=object).copy()
    journal=[]
    par_groupe=collections.defaultdict(collections.Counter)
    for pg in pages:
        ved=vedettes(pg)
        if len(ved)<mini: continue
        sel=np.where(M[:,0]==pg)[0]
        pos={(int(k),int(c)):i for i,(p,k,c) in zip(sel,M[sel])}
        lettres=[]
        for k,i in ved:
            j=pos.get((k,0))
            if j is None: continue
            lettres.append((k,j,tab[lab[j]]))
        if not lettres: continue
        c=collections.Counter(x[2] for x in lettres)
        (maj,n),=c.most_common(1)
        if n/len(lettres) < seuil: continue
        for k,j,ch in lettres:
            if ch!=maj:
                par_groupe[int(lab[j])][maj]+=1
                journal.append((pg,k,ch,maj))
    for g,c in par_groupe.items():
        (maj,n),=c.most_common(1)
        if n>=2:
            tab[g]=maj
    return tab, journal
