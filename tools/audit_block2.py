# -*- coding: utf-8 -*-
"""Does the stored block cover all the text the page carries, on the RIGHT
and at the FOOT?

audit_blockk.py looked only at the foot. Pages photographed askew are
trimmed on the right: « smalto » reads « Vitro blua, obtenat » instead of
« obtenata per la fuzo di materio ». We therefore measure both edges, in
steps of the page's grid -- one column, one line -- and not in pixels.
"""
import sys, os, json, glob, re
import numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT + "/tools")
import page as P
ROOT = _ROOT; T = f"{ROOT}/work"
OUT_PATH = f"{T}/audit_block2.json"


def one_(pg):
    z = np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    a = P.load_(f"{ROOT}/scan/p-{pg:03d}.jpg")
    b = P.mask_edges(P.normalise(a)); _, r = P.deskew(b)
    y0, y1, x0, x1 = P.text_block(r)
    by0, by1, bx0, bx1 = [int(v) for v in z['bloc']]
    vstep = float(z['pasv']); hstep = float(z['pash'])
    return dict(bas_stocke=by1, bas_neuf=int(y1), lignes_perdues=round((y1-by1)/vstep, 2),
                dte_stocke=bx1, dte_neuf=int(x1), colonnes_perdues=round((x1-bx1)/hstep, 2),
                gauche_stocke=bx0, gauche_neuf=int(x0),
                colonnes_gauche=round((bx0-x0)/hstep, 2),
                haut_stocke=by0, haut_neuf=int(y0),
                lignes_haut=round((by0-y0)/vstep, 2))


def all_():
    out = {}
    if os.path.exists(OUT_PATH):
        out = {int(k): v for k, v in json.load(open(OUT_PATH)).items()}
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cells/p-*.npz"))
    for i, pg in enumerate(pages):
        if pg in out: continue
        try: out[pg] = one_(pg)
        except Exception as e: out[pg] = dict(erreur=str(e))
        if i % 50 == 0: print("  %d/%d" % (i, len(pages)), flush=True)
    json.dump(out, open(OUT_PATH, "w"), indent=0)
    return out


if __name__ == "__main__":
    d = all_()
    def engraved(key_, threshold=0.8):
        return sorted(p for p, v in d.items() if v.get(key_, 0) >= threshold)
    for key_ in ('lignes_perdues', 'colonnes_perdues', 'colonnes_gauche', 'lignes_haut'):
        g = engraved(key_)
        print("%-18s : %3d pages  %s" % (key_, len(g), g[:60]))
