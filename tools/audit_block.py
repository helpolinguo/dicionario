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
sys.path.insert(0, '/root/dicionario/outils')
import page as P
RAC = "/root/dicionario"; T = f"{RAC}/travail"
SORTIE = f"{T}/audit_bloc.json"


def une(pg):
    z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    a = P.charger(f"{RAC}/scan/p-{pg:03d}.jpg")
    b = P.masquer_bords(P.normaliser(a)); _, r = P.desincliner(b)
    y0, y1, x0, x1 = P.bloc_texte(r)
    lg = np.array(z['lignes']); pasv = float(z['pasv'])
    perdu = (int(y1) - int(z['bloc'][1])) / pasv
    return dict(stocke=int(z['bloc'][1]), neuf=int(y1), pasv=pasv,
                lignes=len(lg), derniere=float(lg[-1, 1]),
                lignes_perdues=round(perdu, 2))


def tous(debut=0, fin=None):
    out = {}
    if os.path.exists(SORTIE):
        out = {int(k): v for k, v in json.load(open(SORTIE)).items()}
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages = [p for p in pages if p >= debut and (fin is None or p < fin)]
    for i, pg in enumerate(pages):
        if pg in out: continue
        try: out[pg] = une(pg)
        except Exception as e: out[pg] = dict(erreur=str(e))
        if i % 40 == 0: print("  %d/%d (p%03d)" % (i, len(pages), pg), flush=True)
    json.dump(out, open(SORTIE, "w"), indent=0)
    graves = {p: v for p, v in out.items() if v.get('lignes_perdues', 0) >= 0.8}
    print("pages auditees : %d ; pages perdant au moins une ligne : %d"
          % (len(out), len(graves)))
    return graves


if __name__ == "__main__":
    d = int(sys.argv[1]); f = int(sys.argv[2]) if len(sys.argv) > 2 else None
    g = tous(d, f)
    for p in sorted(g)[:40]:
        print("  p%03d : bloc %d -> %d, %.1f ligne(s) perdue(s)"
              % (p, g[p]['stocke'], g[p]['neuf'], g[p]['lignes_perdues']))
