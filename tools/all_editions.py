# -*- coding: utf-8 -*-
"""Rebuilds the two editions of the cleaned text, in the right order.

The HTML page and the pocket dictionary come from the SAME file,
work/edicioni/dicionario.jsonl. Rebuilding them together is the only way to
keep them from diverging: any correction laid in the proofreading layers is
found in the one as in the other.

    python3 tools/all_editions.py            # everything
    python3 tools/all_editions.py --no-base  # without recomputing the base
"""
import os, subprocess, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = _ROOT


def _run(cmd, folder=None, timeout=1800):
    print("  $ %s" % " ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=folder or ROOT, capture_output=True,
                       text=True, timeout=timeout)
    if r.returncode:
        print(r.stdout[-1500:]); print(r.stderr[-1500:])
        raise SystemExit("FAILED: %s" % " ".join(cmd))
    return r.stdout


def run_step(base_=True):
    if base_:
        print("1. the lexical base (edition.py)")
        print(_run([sys.executable, "-u", "tools/edition.py"])[-400:])
    print("2. the HTML page (export.py)")
    print(_run([sys.executable, "-u", "tools/export.py"])[-200:])
    print("3. the text of the pocket book (pocket.py)")
    print(_run([sys.executable, "-u", "tools/pocket.py"])[-200:])
    print("4. typesetting the pocket book (lualatex, two passes)")
    for _ in range(2):
        _run(["lualatex", "-interaction=nonstopmode", "-halt-on-error",
                "posho.tex"], folder=f"{ROOT}/pocket")
    for f in ("index.html", "dicionario.tsv", "dicionario.jsonl"):
        _run(["cp", f"{ROOT}/work/edicioni/{f}", f"{ROOT}/{f}"])
    # The pocket PDF takes at the root the name the page's button points at:
    # index.html and dicionario.pdf travel together.
    _run(["cp", f"{ROOT}/pocket/posho.pdf", f"{ROOT}/dicionario.pdf"])
    print("done: index.html and pocket/posho.pdf come from the same source")


if __name__ == "__main__":
    run_step(base_="--no-base" not in sys.argv)
