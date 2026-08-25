"""Constitution d'un jeu etiquete a la main : une transcription verifiee par page."""
import numpy as np, glob, os
T="/root/dicionario/travail"
def lire(fichier):
    d={}
    for l in open(fichier, encoding='utf-8'):
        l=l.rstrip("\n")
        if not l or l.startswith("#"): continue
        k,_,s=l.partition("\t"); d[int(k)]=s
    return d
def paires(pg, txt):
    """Retourne (indices de cellules dans meta_all, caracteres)."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    occ=z['occ']; lg=z['lignes']
    M=np.load(f"{T}/meta_all.npy")
    sel=np.where(M[:,0]==pg)[0]
    pos={(int(k),int(c)):i for i,(p,k,c) in zip(sel, M[sel])}
    ncol=occ.shape[1]
    idx=[]; car=[]; manques=[]
    for k,s in txt.items():
        s=s.ljust(ncol)
        for c in range(ncol):
            ch=s[c]
            if (k,c) not in pos:
                if ch!=" ": manques.append((k,c,ch))
                continue
            # cellule encree : soit un caractere, soit une bavure -> classe espace
            idx.append(pos[(k,c)]); car.append(ch)
    return np.array(idx), np.array(car, dtype=object), manques
def tout(reps=(f"{T}/amorce", f"{T}/amorce_folios")):
    I=[];C=[];Mq=[]
    fichiers=[]
    for r in reps: fichiers += sorted(glob.glob(r+"/p*.txt"))
    for f in fichiers:
        pg=int(os.path.basename(f)[1:4])
        i,c,mq=paires(pg, lire(f))
        I.append(i); C.append(c); Mq+= [(pg,)+m for m in mq]
    return np.concatenate(I), np.concatenate(C), Mq
