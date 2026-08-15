# -*- coding: utf-8 -*-
"""Rekonstruktas la du edituri de la texto epurita, en la justa ordino.

La pagino HTML e la dicionario de posho venas de la SAMA dosiero,
travail/edicioni/dicionario.jsonl. Rekonstruktar li kune esas la sola maniero
por ke li ne divergez : irga korekto pozita en la kushi di relekto trovesas
en l'una kam en l'altra.

    python3 outils/tout_edituri.py            # omno
    python3 outils/tout_edituri.py --sen-baz  # sen rekalkular la bazo
"""
import os, subprocess, sys
RAC = "/root/dicionario"


def _kurar(cmd, dosiero=None, timeout=1800):
    print("  $ %s" % " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=dosiero or RAC, capture_output=True,
                       text=True, timeout=timeout)
    if r.returncode:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        raise SystemExit("ECHEC : %s" % " ".join(cmd))
    return r.stdout


def executer(baz=True):
    if baz:
        print("1. bazo lexikala (edition.py)")
        print(_kurar([sys.executable, "-u", "outils/edition.py"])[-400:])
    print("2. pagino HTML (exportar.py)")
    print(_kurar([sys.executable, "-u", "outils/exportar.py"])[-200:])
    print("3. texto di la posho-libro (posho.py)")
    print(_kurar([sys.executable, "-u", "outils/posho.py"])[-200:])
    print("4. kompozo di la posho-libro (lualatex, du pasi)")
    for _ in range(2):
        _kurar(["lualatex", "-interaction=nonstopmode", "-halt-on-error",
                "posho.tex"], dosiero=f"{RAC}/posho")
    for f in ("index.html", "dicionario.tsv", "dicionario.jsonl"):
        _kurar(["cp", f"{RAC}/travail/edicioni/{f}", f"{RAC}/{f}"])
    # Le PDF de poche prend a la racine le nom vers lequel pointe le bouton de
    # la pagino : index.html e dicionario.pdf voyajas kune.
    _kurar(["cp", f"{RAC}/posho/posho.pdf", f"{RAC}/dicionario.pdf"])
    print("kompleta : index.html e posho/posho.pdf venas de la sama fonto")


if __name__ == "__main__":
    executer(baz="--sen-baz" not in sys.argv)
