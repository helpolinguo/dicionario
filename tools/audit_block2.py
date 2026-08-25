# -*- coding: utf-8 -*-
"""Le bloc stocke couvre-t-il tout le texte que la page porte, a DROITE et en BAS ?

audit_block.py ne regardait que le bas. Les pages photographiees de biais sont
rognees a droite : « smalto » se lit « Vitro blua, obtenat » au lieu de
« obtenata per la fuzo di materio ». On mesure donc les deux bords, en pas de
la grille de la page — une colonne, une ligne —, et non en pixels.
"""
import sys, os, json, glob, re
import numpy as np
sys.path.insert(0, '/root/dicionario/outils')
import page as P
RAC = "/root/dicionario"; T = f"{RAC}/travail"
SORTIE = f"{T}/audit_bloc2.json"


def une(pg):
    z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    a = P.charger(f"{RAC}/scan/p-{pg:03d}.jpg")
    b = P.masquer_bords(P.normaliser(a)); _, r = P.desincliner(b)
    y0, y1, x0, x1 = P.bloc_texte(r)
    by0, by1, bx0, bx1 = [int(v) for v in z['bloc']]
    pasv = float(z['pasv']); pash = float(z['pash'])
    return dict(bas_stocke=by1, bas_neuf=int(y1), lignes_perdues=round((y1-by1)/pasv, 2),
                dte_stocke=bx1, dte_neuf=int(x1), colonnes_perdues=round((x1-bx1)/pash, 2),
                gauche_stocke=bx0, gauche_neuf=int(x0),
                colonnes_gauche=round((bx0-x0)/pash, 2),
                haut_stocke=by0, haut_neuf=int(y0),
                lignes_haut=round((by0-y0)/pasv, 2))


def tous():
    out = {}
    if os.path.exists(SORTIE):
        out = {int(k): v for k, v in json.load(open(SORTIE)).items()}
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cellules/p-*.npz"))
    for i, pg in enumerate(pages):
        if pg in out: continue
        try: out[pg] = une(pg)
        except Exception as e: out[pg] = dict(erreur=str(e))
        if i % 50 == 0: print("  %d/%d" % (i, len(pages)), flush=True)
    json.dump(out, open(SORTIE, "w"), indent=0)
    return out


if __name__ == "__main__":
    d = tous()
    def graves(cle, seuil=0.8):
        return sorted(p for p, v in d.items() if v.get(cle, 0) >= seuil)
    for cle in ('lignes_perdues', 'colonnes_perdues', 'colonnes_gauche', 'lignes_haut'):
        g = graves(cle)
        print("%-18s : %3d pages  %s" % (cle, len(g), g[:60]))
