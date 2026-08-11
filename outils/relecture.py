# -*- coding: utf-8 -*-
"""Relecture directe, page par page : l'image du scan contre le texte decode.

Toutes les methodes precedentes etaient indirectes — regrouper les formes,
etiqueter les groupes, corriger par le lexique. Elles ont porte le livre de
93 % a un peu plus de 99 %, mais 99 % laisse encore une dizaine de fautes par
page. Pour aller au-dela il faut lire.

La grille rend la chose exacte : une cellule, un caractere. Le relecteur recoit
donc chaque ligne decodee et doit rendre une ligne de **meme longueur**. Une
lettre manquante remplace une espace, une lettre de trop redevient une espace,
et le rapprochement se fait colonne par colonne, sans ambiguite.
"""
import numpy as np, os, sys, json
from PIL import Image, ImageDraw
sys.path.insert(0,'/root/dicionario/outils')
RAC="/root/dicionario"; T=f"{RAC}/travail"
ZOOM=1.7; BANDES=3; CHEV=2      # chevauchement, en lignes

def texte_page(pg, pages=None):
    if pages is None:
        from edition import charger_texte
        pages,_=charger_texte()
    return pages.get(pg, [])

def bandes(pg, rep, lignes):
    """Decoupe la page en bandes horizontales, chacune lisible d'un coup."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    ech=float(z['shape'][0])/Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").size[1]
    pasv=float(z['pasv']); lg={int(k):float(y) for k,y in z['lignes']}
    im=Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')
    W,H=im.size
    ks=sorted(lg)
    n=max(1,(len(ks)+BANDES-1)//BANDES)
    out=[]
    for b in range(0, len(ks), n):
        sous=ks[max(b-CHEV,0): b+n+CHEV]
        if not sous: continue
        y0=max(int((lg[sous[0]]-1.2*pasv)/ech), 0)
        y1=min(int((lg[sous[-1]]+1.2*pasv)/ech), H)
        c=im.crop((0,y0,W,y1))
        c=c.resize((int(W*ZOOM), int((y1-y0)*ZOOM)), Image.LANCZOS)
        nom=f"{rep}/p{pg:03d}b{b//n}.png"; c.save(nom)
        out.append(dict(fichier=os.path.basename(nom), lignes=[k for k in ks[b:b+n]]))
    return out

def preparer(pgs, rep=f"{T}/relecture"):
    os.makedirs(rep, exist_ok=True)
    from edition import charger_texte
    pages,_=charger_texte()
    fiches=[]
    for pg in pgs:
        lignes=dict(texte_page(pg, pages))
        bs=bandes(pg, rep, lignes)
        with open(f"{rep}/p{pg:03d}.txt","w",encoding='utf-8') as f:
            for b in bs:
                f.write(f"== {b['fichier']}\n")
                for k in b['lignes']:
                    f.write(f"{k:03d}|{lignes.get(k,'')}\n")
        fiches.append(dict(pagino=pg, bandes=bs))
    json.dump(fiches, open(f"{rep}/fiches.json","w"))
    return fiches

if __name__=="__main__":
    pgs=[int(x) for x in sys.argv[1:]]
    f=preparer(pgs)
    print("pages preparees :", len(f), " bandes :", sum(len(x['bandes']) for x in f))
