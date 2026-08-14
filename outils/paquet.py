# -*- coding: utf-8 -*-
"""Paquet de livraison : les sources du projet + le PDF compose.

On exclut ce qui est reconstructible et lourd — le scan, le corpus de
cellules, le corpus de traits, les planches de relecture. Tout le reste tient
en une quinzaine de megaoctets.
"""
import os, shutil, zipfile, glob
RAC="/root/dicionario"; T=f"{RAC}/travail"
SORTIE="/root/dicionario-source.zip"

FICHIERS = ["main.tex", "preambule.tex", "LISEZ-MOI.md", "main.pdf",
            "dicionario.html", "dicionario.tsv", "dicionario.jsonl"]
DOSSIERS = ["outils", "contenu", "ornements", "posho"]
CORRECTIONS = ["exceptions.txt", "exceptions_manuel.txt", "exceptions_fins.txt",
               "exceptions_paires.txt", "exceptions_relecture.txt",
               "exceptions_ornements.txt", "sou_relus.txt",
               "ornements.json", "pages_non_dactylo.txt"]
BINAIRES = ["filets.pkl", "debuts.pkl"]

def executer(sortie=SORTIE):
    if os.path.exists(sortie): os.remove(sortie)
    z=zipfile.ZipFile(sortie, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
    for f in FICHIERS:
        p=os.path.join(RAC,f)
        if os.path.exists(p): z.write(p, f"dicionario/{f}")
    for d in DOSSIERS:
        for p in glob.glob(f"{RAC}/{d}/**/*", recursive=True):
            if os.path.isfile(p) and "__pycache__" not in p:
                z.write(p, "dicionario/"+os.path.relpath(p, RAC))
    for f in CORRECTIONS+BINAIRES:
        p=os.path.join(T,f)
        if os.path.exists(p): z.write(p, f"dicionario/corrections/{f}")
    # Le releve de relecture, page par page — le TEXTE seulement. Le dossier
    # contient aussi les planches images : 550 Mo, reconstructibles a la
    # demande par outils/relecture.py, et sans interet pour qui lit le code.
    for p in sorted(glob.glob(f"{T}/relecture/*")):
        if os.path.isfile(p) and os.path.splitext(p)[1].lower() in (".txt", ".md"):
            z.write(p, "dicionario/relecture/"+os.path.basename(p))
    z.close()
    return sortie, os.path.getsize(sortie)

if __name__=="__main__":
    p,n=executer(); print("%s : %.1f Mo"%(p, n/1e6))
