# -*- coding: utf-8 -*-
"""Is the foot of the stored block the one the code returns today?

Page 116 revealed that its extraction dated from an earlier version of
bloc_texte(): the block stopped there at y=994 where the present code
returns 1071, and four lines of text -- among them the end of the
definition of « dicionario » and the article « diciplinar » -- fell outside
the cutting. This check looks for every page in that case.
"""
import sys, os, json, glob, re
import numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT + "/tools")
import page as P
ROOT = _ROOT; T = f"{ROOT}/travail"
OUT_PATH = f"{T}/audit_bloc.json"


def one_(pg):
    z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    a = P.load_(f"{ROOT}/scan/p-{pg:03d}.jpg")
    b = P.mask_edges(P.normalise(a)); _, r = P.deskew(b)
    y0, y1, x0, x1 = P.bloc_texte(r)
    lg = np.array(z['lignes']); vstep = float(z['pasv'])
    perdu = (int(y1) - int(z['bloc'][1])) / vstep
    return dict(stocke=int(z['bloc'][1]), neuf=int(y1), pasv=vstep,
                lignes=len(lg), derniere=float(lg[-1, 1]),
                lignes_perdues=round(perdu, 2))


def all_(start_=0, end_=None):
    out = {}
    if os.path.exists(OUT_PATH):
        out = {int(k): v for k, v in json.load(open(OUT_PATH)).items()}
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages = [p for p in pages if p >= start_ and (end_ is None or p < end_)]
    for i, pg in enumerate(pages):
        if pg in out: continue
        try: out[pg] = one_(pg)
        except Exception as e: out[pg] = dict(erreur=str(e))
        if i % 40 == 0: print("  %d/%d (p%03d)" % (i, len(pages), pg), flush=True)
    json.dump(out, open(OUT_PATH, "w"), indent=0)
    graves = {p: v for p, v in out.items() if v.get('lignes_perdues', 0) >= 0.8}
    print("pages audited: %d ; pages losing at least one line: %d"
          % (len(out), len(graves)))
    return graves


if __name__ == "__main__":
    d = int(sys.argv[1]); f = int(sys.argv[2]) if len(sys.argv) > 2 else None
    g = all_(d, f)
    for p in sorted(g)[:40]:
        print("  p%03d : block %d -> %d, %.1f line(s) lost"
              % (p, g[p]['stocke'], g[p]['neuf'], g[p]['lignes_perdues']))
