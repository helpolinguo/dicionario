import numpy as np
T="/root/dicionario/travail"

_bav=None
def bavures():
    """Cellules qui ne contiennent qu'une bavure : l'encre y est plaquee contre
    un bord de la cellule.

    - bord gauche/droit : debordement du caractere voisin ;
    - bord haut : hampe d'une parenthese ou d'une majuscule de la ligne
      SUIVANTE, qui depasse dans la cellule vide au-dessus d'elle ;
    - bord bas : jambage ou filet de la ligne precedente.

    Les trois seuils sont calibres sur la transcription-amorce : aucun des
    7 006 caracteres reels verifies a la main n'est perdu."""
    global _bav
    if _bav is None:
        C=np.load(f"{T}/cells_all.npy", mmap_mode='r')
        n=len(C); _bav=np.zeros(n,bool)
        for a in range(0,n,100000):
            A=np.asarray(C[a:a+100000]).astype(np.float32)/255.
            tot=A.sum((1,2))
            bord=(A[:,:,:2].sum((1,2))+A[:,:,-2:].sum((1,2)))/(tot+1e-6)
            haut=A[:,:4,:].sum((1,2))/(tot+1e-6)
            bas=A[:,18:,:].sum((1,2))/(tot+1e-6)
            _bav[a:a+100000]=((bord>0.55)|((tot<12)&(bord>0.25))
                              |(haut>0.80)|(bas>0.85))
    return _bav
def charger():
    lab=np.load(f"{T}/km_lab.npy"); M=np.load(f"{T}/meta_all.npy")
    return lab,M
def table(fichier=f"{T}/etiquettes.txt", n=None):
    """Table groupe -> caractere. Fichier : une ligne 'idx car' (car vide = espace)."""
    props=np.load(f"{T}/proposition.npy")
    tab=np.array(props, dtype=object).copy()
    import os
    if os.path.exists(fichier):
        for l in open(fichier, encoding='utf-8'):
            l=l.rstrip("\n")
            if not l.strip() or l.startswith("#"): continue
            i,_,c=l.partition("\t")
            tab[int(i)]=c
    return tab
def page_texte(pg, lab, M, tab):
    import numpy as np
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=z['lignes']; ncol=z['occ'].shape[1]
    sel=np.where(M[:,0]==pg)[0]
    m=M[sel]; l=lab[sel]
    bv=bavures()[sel]
    par={}
    for (p,k,c),b,x in zip(m,l,bv):
        par.setdefault(int(k),{})[int(c)]=" " if x else tab[b]
    out=[]
    for k in lg[:,0]:
        k=int(k); d=par.get(k,{})
        s="".join(d.get(c," ") for c in range(ncol)).rstrip()
        out.append((k,s))
    return out
