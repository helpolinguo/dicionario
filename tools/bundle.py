# -*- coding: utf-8 -*-
"""The delivery bundle: the project's sources + the composed PDF.

We leave out what is reconstructible and heavy -- the scan, the corpus of
cells, the corpus of features, the proofreading sheets. All the rest fits in
some fifteen megabytes.
"""
import os, shutil, zipfile, glob
RAC="/root/dicionario"; T=f"{RAC}/travail"
SORTIE="/root/dicionario-source.zip"

FICHIERS = ["main.tex", "preamble.tex", "LISEZ-MOI.md", "main.pdf",
            "index.html", "dicionario.tsv", "dicionario.jsonl",
            # The pocket PDF travels BESIDE the page: the download button points at
            # it by a relative link, and the site is published by copying the two
            # files into the same folder.
            "dicionario.pdf"]
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
    # The proofreading survey, page by page -- the TEXT only. The folder also
    # holds the image sheets: 550 MB, reconstructible on demand by
    # tools/proofreading.py, and of no interest to whoever reads the code.
    for p in sorted(glob.glob(f"{T}/relecture/*")):
        if os.path.isfile(p) and os.path.splitext(p)[1].lower() in (".txt", ".md"):
            z.write(p, "dicionario/relecture/"+os.path.basename(p))
    z.close()
    return sortie, os.path.getsize(sortie)

if __name__=="__main__":
    p,n=executer(); print("%s : %.1f Mo"%(p, n/1e6))
