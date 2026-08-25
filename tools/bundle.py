# -*- coding: utf-8 -*-
"""The delivery bundle: the project's sources + the composed PDF.

We leave out what is reconstructible and heavy -- the scan, the corpus of
cells, the corpus of features, the proofreading sheets. All the rest fits in
some fifteen megabytes.
"""
import os, shutil, zipfile, glob
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=_ROOT; T=f"{ROOT}/work"
OUT_PATH=os.path.join(os.path.dirname(_ROOT), "dicionario-source.zip")

FILES = ["main.tex", "preamble.tex", "LISEZ-MOI.md", "main.pdf",
            "index.html", "dicionario.tsv", "dicionario.jsonl",
            # The pocket PDF travels BESIDE the page: the download button points at
            # it by a relative link, and the site is published by copying the two
            # files into the same folder.
            "dicionario.pdf"]
FOLDERS = ["tools", "content", "ornaments", "pocket"]
CORRECTIONS = ["exceptions.txt", "exceptions_manual.txt", "exceptions_ends.txt",
               "exceptions_pairs.txt", "exceptions_proofreading.txt",
               "exceptions_ornaments.txt", "underlines_reread.txt",
               "ornaments.json", "pages_not_typed.txt"]
BINARIES = ["rules.pkl", "starts.pkl"]

def run_step(out_path=OUT_PATH):
    if os.path.exists(out_path): os.remove(out_path)
    z=zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9)
    for f in FILES:
        p=os.path.join(ROOT,f)
        if os.path.exists(p): z.write(p, f"dicionario/{f}")
    for d in FOLDERS:
        for p in glob.glob(f"{ROOT}/{d}/**/*", recursive=True):
            if os.path.isfile(p) and "__pycache__" not in p:
                z.write(p, "dicionario/"+os.path.relpath(p, ROOT))
    for f in CORRECTIONS+BINARIES:
        p=os.path.join(T,f)
        if os.path.exists(p): z.write(p, f"dicionario/corrections/{f}")
    # The proofreading survey, page by page -- the TEXT only. The folder also
    # holds the image sheets: 550 MB, reconstructible on demand by
    # tools/proofreading.py, and of no interest to whoever reads the code.
    for p in sorted(glob.glob(f"{T}/proofreading/*")):
        if os.path.isfile(p) and os.path.splitext(p)[1].lower() in (".txt", ".md"):
            z.write(p, "dicionario/proofreading/"+os.path.basename(p))
    z.close()
    return out_path, os.path.getsize(out_path)

if __name__=="__main__":
    p,n=run_step(); print("%s : %.1f Mo"%(p, n/1e6))
