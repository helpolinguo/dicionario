# -*- coding: utf-8 -*-
"""Decision de casse, cellule par cellule, par comparaison a la ligne elle-meme.

Deux tentatives ont echoue avant celle-ci, et elles disent pourquoi celle-ci
tient.

1. Sommet de l'encre, seuil absolu. Desastreux : la fenetre d'une cellule mord
   sur ses voisines, une moucheture suffit a faire passer un « a » pour un « A ».
2. Sommet de la composante connexe portant le corps de la lettre, seuil absolu.
   Toujours perdant. En regardant enfin les cellules fautives, la raison saute
   aux yeux : sur certaines pages les bas de casse montent aussi haut, en
   rangees de la trame, que les capitales d'autres pages. L'echelle du scan
   n'est pas constante ; un seuil absolu ne mesure donc rien.

D'ou la regle retenue : on ne compare pas une lettre a un seuil, on la compare
aux lettres de sa propre ligne. Toute ligne de ce dictionnaire contient des
hampes — « b d f h k l t » — qui montent a la hauteur des capitales, et des
lettres a hauteur d'x — « a c e m n o r s u v w x z » — qui s'arretent a
mi-corps. Ces deux reperes donnent l'echelle de la ligne. Une lettre a hauteur
d'x qui monte du cote des hampes est une capitale.
"""
import numpy as np, sys
from scipy.ndimage import label as cclabel
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"
XH  = "acemnorsuvwxz"     # hauteur d'x : c'est sur elles que porte le doute
HAMPE = "bdfhklt"         # hampes : elles donnent la hauteur des capitales
MINI = 4                  # reperes minimaux de chaque sorte sur la ligne
PART = 0.35               # fraction du chemin hampe -> hauteur d'x
_ST = np.ones((3,3),int)

def sommet_lettre(A):
    """Sommet de la composante connexe qui porte le corps de la lettre."""
    B=(A>60); n=len(A); som=np.full(n,np.nan)
    for i in range(n):
        b=B[i]
        if b.sum()<4: continue
        L,k=cclabel(b, structure=_ST)
        if k==0: continue
        best=0; sc=-1
        for j in range(1,k+1):
            s=int((L[8:15]==j).sum())
            if s>sc: sc=s; best=j
        if sc<=0: continue
        w=np.where((L==best).any(1))[0]
        if len(w): som[i]=w[0]
    return som

def executer(sortie=f"{T}/exceptions_casse.txt"):
    C=np.load(f"{T}/cells_all.npy", mmap_mode='r'); M=np.load(f"{T}/meta_all.npy")
    kl=np.load(f"{T}/km_lab.npy"); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    from decoder import bavures
    bv=bavures()
    car=np.array([str(tab[k]) for k in range(len(tab))], dtype=object)
    # regroupement par ligne
    cle = M[:,0].astype(np.int64)*10000 + M[:,1].astype(np.int64)
    o=np.argsort(cle, kind='stable'); bornes=np.flatnonzero(np.r_[True, np.diff(cle[o])!=0, True])
    ecrit=0; lignes=0
    with open(sortie,"w",encoding='utf-8') as f:
        f.write("# Casse tranchee par comparaison aux hampes de la meme ligne.\n")
        f.write("# Priorite basse : toute correction a la main l'emporte.\n")
        for a,b in zip(bornes[:-1], bornes[1:]):
            g=o[a:b]
            g=g[~bv[g]]
            if len(g)<8: continue
            c=car[kl[g]]
            mx=np.array([x in XH for x in c]); mh=np.array([x in HAMPE for x in c])
            if mx.sum()<MINI or mh.sum()<MINI: continue
            som=sommet_lettre(np.asarray(C[np.sort(g)]).astype(np.float32))
            som=som[np.argsort(np.argsort(g))]      # remettre dans l'ordre de g
            sx=np.nanmedian(som[mx]); sh=np.nanmedian(som[mh])
            if np.isnan(sx) or np.isnan(sh) or sx-sh < 1.5: continue
            seuil = sh + PART*(sx-sh)
            lignes+=1
            for i in np.where(mx)[0]:
                if np.isnan(som[i]) or som[i]>seuil: continue
                pg,k,cc=M[g[i]]
                f.write(f"{int(pg)}\t{int(k)}\t{int(cc)}\t{c[i].upper()}\n"); ecrit+=1
    print("lignes calibrees :",lignes," cellules passees en capitale :",ecrit)

if __name__=="__main__": executer()
