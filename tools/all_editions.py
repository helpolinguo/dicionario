# -*- coding: utf-8 -*-
"""Rebuilds the two editions of the cleaned text, in the right order.

The HTML page and the pocket dictionary come from the SAME file,
work/edicioni/dicionario.jsonl. Rebuilding them together is the only way to
keep them from diverging: any correction laid in the proofreading layers is
found in the one as in the other.

    python3 tools/all_editions.py            # everything
    python3 tools/all_editions.py --sen-baz  # without recomputing the base
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
        print(_kurar([sys.executable, "-u", "tools/edition.py"])[-400:])
    print("2. pagino HTML (export.py)")
    print(_kurar([sys.executable, "-u", "tools/export.py"])[-200:])
    print("3. texto di la posho-libro (pocket.py)")
    print(_kurar([sys.executable, "-u", "tools/pocket.py"])[-200:])
    print("4. kompozo di la posho-libro (lualatex, du pasi)")
    for _ in range(2):
        _kurar(["lualatex", "-interaction=nonstopmode", "-halt-on-error",
                "posho.tex"], dosiero=f"{RAC}/posho")
    for f in ("index.html", "dicionario.tsv", "dicionario.jsonl"):
        _kurar(["cp", f"{RAC}/work/edicioni/{f}", f"{RAC}/{f}"])
    # The pocket PDF takes at the root the name the page's button points at:
    # index.html and dicionario.pdf travel together.
    _kurar(["cp", f"{RAC}/pocket/posho.pdf", f"{RAC}/dicionario.pdf"])
    print("kompleta : index.html e pocket/posho.pdf venas de la sama fonto")


if __name__ == "__main__":
    executer(baz="--sen-baz" not in sys.argv)
