"""Prepare les planches de relecture d'une page : une ligne du livre par ligne
d'image, colonnes numerotees, plus le decodage courant en regard."""
import sys, os, numpy as np
sys.path.insert(0,'/root/dicionario/outils')
from line_images import image_lignes
from decode import charger, page_texte
from generate import exceptions
T="/root/dicionario/travail"

def preparer(pg, rep=None, par=12, zoom=4):
    rep = rep or f"{T}/relecture/p{pg:03d}"
    os.makedirs(rep, exist_ok=True)
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    c=z['cells']; lg=z['lignes']; occ=z['occ']
    for a in range(0, c.shape[0], par):
        image_lignes(c[a:a+par], lignes_ids=[int(x) for x in lg[a:a+par,0]], zoom=zoom
                     ).save(f"{rep}/planche{a//par:02d}.png")
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy", allow_pickle=True)
    exc=exceptions()
    lignes=[]
    for k,s in page_texte(pg,lab,M,tab):
        l=list(s)
        for (pp,kk,cc),v in exc.items():
            if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
        lignes.append((k,"".join(l).rstrip()))
    with open(f"{rep}/decodage.txt","w",encoding='utf-8') as f:
        for k,s in lignes: f.write(f"{k}\t{s}\n")
    with open(f"{rep}/occupation.txt","w",encoding='utf-8') as f:
        for i,k in enumerate(lg[:,0]):
            f.write(f"{int(k)}\t" + "".join("#" if o else "." for o in occ[i]) + "\n")
    return rep, (c.shape[0]+par-1)//par

if __name__=="__main__":
    for a in sys.argv[1:]:
        print(preparer(int(a)))
