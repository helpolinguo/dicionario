# -*- coding: utf-8 -*-
"""Combien de caracteres le bloc coupe-t-il en fin de ligne ? Mesure, pas avis.

On recoupe chaque page avec le bloc etendu a droite — sans rien enregistrer —
et on compte les cellules occupees qui tombent au-dela du bloc actuel. Ce sont
exactement les caracteres perdus.
"""
import sys, os, json
import numpy as np
sys.path.insert(0,'/root/dicionario/outils')
import cells
RAC="/root/dicionario"; T=f"{RAC}/travail"

def une(pg):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    ncol=z['occ'].shape[1]; col0=int(z['col0'])
    cellules.ETENDRE=False; cellules.ETENDRE_D=True
    d=cellules.extraire(f"{RAC}/scan/p-{pg:03d}.jpg")
    occ=d['occ']; c0=int(d['col0'])
    # colonnes de l'extension : au-dela de (col0-c0) + ncol dans le repere etendu
    debut=(col0-c0)+ncol
    if debut >= occ.shape[1]: return dict(pagino=pg, perdus=0, lignes=0, colonnes=0)
    sup=occ[:, debut:]
    lignes=int((sup.sum(1)>0).sum())
    return dict(pagino=pg, perdus=int(sup.sum()), lignes=lignes,
                colonnes=int(occ.shape[1]-debut))

if __name__=="__main__":
    a,b=int(sys.argv[1]), int(sys.argv[2]); out=[]
    for pg in range(a,b):
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        if pg in (0,1,3,7,87,111,577): continue
        try: out.append(une(pg))
        except Exception as e: print("ECHEC",pg,e, flush=True)
    json.dump(out, open(f"{T}/fins_{a}.json","w"))
    p=sum(x['perdus'] for x in out); l=sum(x['lignes'] for x in out)
    print(f"{a}-{b} : {len(out)} pages, {l} lignes touchees, {p} caracteres coupes")
