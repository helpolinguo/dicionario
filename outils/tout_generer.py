# -*- coding: utf-8 -*-
"""Genere les 639 pages du fac-simile, y compris ce qui n'est pas de la frappe.

Trois sortes de pages echappent a la grille et sont traitees a part :
la couverture, qui est une lithographie ; les six pages blanches ; et les
pages qui portent un ornement — la signature autographe de l'auteur sur la
page de contrefacon, la lettre de l'alphabet en grand corps en tete de chaque
section. L'ornement est decoupe dans le scan et repose a sa place, mesuree en
fraction de feuille, sans occuper de place dans la grille.
"""
import numpy as np, sys, os, json
sys.path.insert(0,'/root/dicionario/outils')
from decoder import charger
from generer import ecrire
T="/root/dicionario/travail"; RAC="/root/dicionario"
LARG=210.0; HAUT=297.0; ORIGX=21.9; ORIGY=12.44
MARGE={'signaturo':10}          # marge du decoupage, en pixels du scan

def non_dactylo():
    d={}
    p=f"{T}/pages_non_dactylo.txt"
    if os.path.exists(p):
        for l in open(p,encoding='utf-8'):
            if l.startswith('#') or not l.strip(): continue
            a,b=l.rstrip('\n').split('\t'); d[int(a)]=b
    return d

def ornements():
    """Ornements par page — une LISTE par page, et non un seul ornement.

    Le dictionnaire {page: ornement} perdait le second ornement d'une page qui
    en porte deux. La page 631 en porte justement deux : le « X » en tete, et
    le « Y » au milieu, la section Y ne s'ouvrant pas sur une feuille neuve.
    Le « Y » y disparaissait sans bruit.
    """
    p=f"{T}/ornements.json"
    if not os.path.exists(p): return {}
    d={}
    for e in json.load(open(p)): d.setdefault(e['pagino'], []).append(e)
    return d

PASH_MM=2.540; PASV_MM=4.321      # le pas de la machine, en millimetres

def _latex_ornement(e):
    """Position de l'ornement en coordonnees de GRILLE, pas en fraction de feuille.

    Premiere version : la position etait exprimee en fraction de la feuille
    scannee. Elle tombait a cote — le cadrage du scan varie d'une page a
    l'autre, alors que la grille, elle, ne varie pas. On convertit donc la
    boite de l'ornement en colonnes et en lignes de la grille de sa page, puis
    on la repose au pas de la machine. C'est le meme invariant que le texte,
    donc le meme calage.
    """
    m=MARGE.get(e['litero'], 6)
    pg=e['pagino']
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    ech=float(z['shape'][0])/e['H']
    pasv=float(z['pasv']); pash=float(z['pash'])
    xg=float(z['xg']); col0=int(z['col0']); lg=z['lignes']
    y0=float(lg[0][1])
    col=((e['x']-m)*ech - xg)/pash - col0
    lig=(((e['y']+e['h']+m)*ech) - y0)/pasv
    lar=((e['w']+2*m)*ech)/pash
    return ("\\marge[%.3fmm]{%.3fmm}{\\ornamento{%.3fmm}{%s}}"
            % (col*PASH_MM, lig*PASV_MM, lar*PASH_MM, e['dosiero']))

def executer():
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True)
    nd=non_dactylo(); orn=ornements()
    n=int(M[:,0].max())+1; faites=[]
    for pg in range(n):
        chemin=f"{RAC}/contenu/p{pg:03d}.tex"
        if pg in nd:
            corps=("\\pgimago{ornements/couverture/couverture.pdf}"
                   if nd[pg]=='kovrilo' else "\\pgvakua")
            note = "couverture, lithographie" if nd[pg]=='kovrilo' else "page blanche"
            open(chemin,"w",encoding='utf-8').write(
                "%% page %d du fac-simile (image p-%03d) — %s, pas de frappe\n%s\n"
                % (pg+1, pg, note, corps))
            faites.append(pg); continue
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        try: ecrire(pg,lab,M,tab)
        except Exception as e:
            print("ECHEC p%03d : %s"%(pg,e), flush=True); continue
        if pg in orn:
            L=open(chemin,encoding='utf-8').read().split("\n")
            # Tous les ornements de la page, poses sur la premiere ligne : leur
            # place est donnee en coordonnees de grille par \marge, donc l'un
            # comme l'autre tombe ou il doit, quelle que soit la ligne d'accueil.
            tete="".join(_latex_ornement(e) for e in orn[pg])
            for i,l in enumerate(L):
                if l.startswith("\\l{"):
                    L[i]="\\l{"+tete+l[3:]
                    break
            else:
                for i,l in enumerate(L):
                    if l=="\\pg{":
                        L.insert(i+1,"\\l{"+tete+"}"); break
            open(chemin,"w",encoding='utf-8').write("\n".join(L))
        faites.append(pg)
        if pg%100==0: print("  ...p%03d"%pg, flush=True)
    # Feuillet de garde. Le livre se termine sur « F I N O », en page 639 —
    # nombre impair, et sans garde. Une page blanche de plus le porte a 640,
    # soit quarante cahiers de seize : ce qu'il faut pour le relier. La garde
    # de tete existe deja dans le livre (les pages blanches du scan).
    open(f"{RAC}/contenu/garde.tex","w",encoding='utf-8').write(
        "%% feuillet de garde final : porte le livre a 640 pages, quarante cahiers de seize\n\\pgvakua\n")
    with open(f"{RAC}/contenu/toutes.tex","w",encoding='utf-8') as f:
        for pg in faites: f.write("\\input{contenu/p%03d}\n"%pg)
        f.write("\\input{contenu/garde}\n")
    print("pages ecrites :", len(faites), "| non dactylographiees :", len(nd),
          "| ornees :", len([p for p in orn if p in faites]))

if __name__=="__main__": executer()
