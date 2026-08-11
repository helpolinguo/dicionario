# -*- coding: utf-8 -*-
"""Inventaire de ce qui n'est pas dactylographie.

Le livre n'est pas tout entier une grille de caracteres. Il porte aussi :
la couverture, qui est une lithographie ; des pages blanches ; la signature
autographe de l'auteur sur la page de contrefacon ; et, en tete de chaque
lettre de l'alphabet, cette lettre composee en grand corps dans une elzevir.
Aucun de ces elements ne se decode : ils se reperent, se mesurent et se
reproduisent tels quels.

Le repere est sans echelle : sur une page dactylographiee, toutes les taches
d'encre ont sensiblement la meme hauteur. Ce qui depasse nettement la hauteur
mediane de la page n'appartient pas a la frappe.
"""
import numpy as np, os, sys, json
from scipy.ndimage import label as cclabel, find_objects
from PIL import Image
sys.path.insert(0,'/root/dicionario/outils')
RAC="/root/dicionario"; T=f"{RAC}/travail"
_ST=np.ones((3,3),int)

def analyser_page(pg):
    a=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    b = a < (a.mean()-0.28*a.std())
    # on ignore la bande d'ombre des bords
    m=int(0.03*min(H,W)); b[:m]=False; b[-m:]=False; b[:,:m]=False; b[:,-m:]=False
    L,k=cclabel(b, structure=_ST)
    if k==0: return dict(pagino=pg, encre=0, blanka=True, elementi=[])
    obj=find_objects(L)
    haut=np.array([o[0].stop-o[0].start for o in obj])
    larg=np.array([o[1].stop-o[1].start for o in obj])
    aire=np.array([int((L[o]==i+1).sum()) for i,o in enumerate(obj)])
    gros=aire>=25
    if gros.sum()<20:
        return dict(pagino=pg, encre=int(aire.sum()), blanka=True, elementi=[])
    hm=float(np.median(haut[gros]))
    el=[]
    for i,o in enumerate(obj):
        if aire[i]<200: continue
        if haut[i] < 2.2*hm and larg[i] < 6*hm: continue
        el.append(dict(y=int(o[0].start), x=int(o[1].start),
                       h=int(haut[i]), w=int(larg[i]), aire=int(aire[i]),
                       hauteur_relative=round(haut[i]/hm,2)))
    el.sort(key=lambda e:-e['aire'])
    return dict(pagino=pg, encre=int(aire.sum()), blanka=False,
                hauteur_mediane=round(hm,1), elementi=el[:12])

def executer(sortie=f"{T}/horsgrille.json"):
    out=[]
    for pg in range(639):
        if not os.path.exists(f"{RAC}/scan/p-{pg:03d}.jpg"): continue
        try: out.append(analyser_page(pg))
        except Exception as e: out.append(dict(pagino=pg, erreur=str(e)))
        if pg%50==0: print("  ...p%03d"%pg, flush=True)
    json.dump(out, open(sortie,'w'), ensure_ascii=False)
    bl=[o['pagino'] for o in out if o.get('blanka')]
    ho=[(o['pagino'], len(o['elementi'])) for o in out if o.get('elementi')]
    print("pages blanches :", len(bl), bl)
    print("pages portant un element hors grille :", len(ho))
    print(ho[:60])

if __name__=="__main__": executer()
