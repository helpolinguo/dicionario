# -*- coding: utf-8 -*-
"""Rend les DEBUTS de ligne que le bloc coupait — le pendant gauche de
rendre_fins.py.

Le bloc de texte est cerne par les colonnes encrees sur au moins trois lignes.
A droite, cela coupait des fins de mots ; a gauche, cela coupe la premiere
lettre des lignes que la dactylo a commencees une cellule plus tot que les
autres. Le mal est plus grave de ce cote, parce que ces lignes-la sont
justement les vedettes : « protezo » se lisait « rotezo », « protisto »
« rotisto », « sorgumo » « orgumo ».

On ne redecoupe pas le livre pour autant — l'elargissement du bloc oblige a
tout recouper, ce qui avait fait perdre des vedettes a cent quarante-cinq
pages. On recoupe donc chaque page EN MEMOIRE avec le bloc etendu a gauche, on
rattache les cellules recuperees au groupe dont le centre est le plus proche
dans l'espace traits2, et on les depose a part. Le decoupage enregistre ne
bouge pas : aucune correction deja faite n'est invalidee.

La difference avec le cote droit tient a la numerotation. A droite, les
cellules recuperees prennent les colonnes qui suivent le bloc : rien ne bouge.
A gauche, elles tombent AVANT la colonne zero. Les renumeroter en decalant la
seule ligne concernee serait faux — elle se retrouverait une cellule a droite
de sa place reelle. On decale donc la PAGE ENTIERE d'autant de cellules qu'il
en manque : les positions relatives sont conservees au caractere pres, et le
bloc, dont la marge est fixee par ailleurs, retombe au meme endroit sur la
feuille. C'est generer.lignes_page() qui applique ce decalage, en decalant
aussi les plages de soulignement.
"""
import sys, os, pickle, glob, re
import numpy as np
sys.path.insert(0, '/root/dicionario/outils')
import cellules
from traits2 import traits2
RAC = "/root/dicionario"; T = f"{RAC}/travail"


def une(pg, Q, tab):
    """Caracteres recuperes a gauche du bloc : {ligne: {colonne negative: car}}."""
    z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    col0 = int(z['col0'])
    cles = set(int(k) for k, _ in z['lignes'])
    cellules.ETENDRE = True; cellules.ETENDRE_D = False; cellules.ETENDRE_FORCE = 2
    try:
        d = cellules.extraire(f"{RAC}/scan/p-{pg:03d}.jpg")
    finally:
        cellules.ETENDRE = False; cellules.ETENDRE_FORCE = 0
    lg = np.array(d['lignes'])
    if set(int(k) for k in lg[:, 0]) != cles:
        return None, "lignes differentes"
    delta = col0 - int(d['col0'])
    if delta <= 0:
        return {}, None
    occ = d['occ']
    ii, jj = np.where(occ[:, :delta])
    if not len(ii):
        return {}, None
    A = (np.clip(d['nues'][ii, jj], 0, 1) * 255.0).round().astype(np.uint8)
    P = A.astype(np.float32) / 255.
    tot = P.sum((1, 2))
    bord = (P[:, :, :2].sum((1, 2)) + P[:, :, -2:].sum((1, 2))) / (tot + 1e-6)
    haut = P[:, :4, :].sum((1, 2)) / (tot + 1e-6)
    bas = P[:, 18:, :].sum((1, 2)) / (tot + 1e-6)
    bav = ((bord > 0.55) | ((tot < 12) & (bord > 0.25)) | (haut > 0.80) | (bas > 0.85))
    X = traits2(A); X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-6)
    g = (X @ Q.T).argmax(1)
    out = {}
    for i in range(len(ii)):
        if bav[i]:
            continue
        ch = str(tab[g[i]])
        if ch == ' ' or len(ch) != 1:
            continue
        out.setdefault(int(lg[ii[i], 0]), {})[int(jj[i]) - delta] = ch
    return out, None


def tous(sortie=f"{T}/debuts.pkl", debut=0, fin=None):
    Q = np.load(f"{T}/km_centres2.npy")
    tab = np.load(f"{T}/cls_lab.npy", allow_pickle=True)
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages = [p for p in pages if p >= debut and (fin is None or p < fin)]
    out = {}; refus = 0
    for i, pg in enumerate(pages):
        try:
            r, err = une(pg, Q, tab)
        except Exception as e:
            print("ECHEC p%03d : %s" % (pg, e), flush=True); continue
        if r is None:
            refus += 1
        elif r:
            out[pg] = r
            print("  p%03d : %s" % (pg, sorted((k, "".join(v[c] for c in sorted(v)))
                                               for k, v in r.items())), flush=True)
        if i % 50 == 0:
            print("  ...%d/%d" % (i, len(pages)), flush=True)
    with open(sortie, "wb") as f:
        pickle.dump(out, f)
    print("pages avec un debut recupere : %d ; pages refusees : %d" % (len(out), refus))
    return out


if __name__ == "__main__":
    tous()
