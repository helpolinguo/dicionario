# -*- coding: utf-8 -*-
"""Gives back the line STARTS the block was cutting off — the left-hand
counterpart of restore_ends.py.

The block of text is bounded by the columns inked on at least three lines. On
the right, that cut off the ends of words; on the left, it cuts off the first
letter of the lines the typist began one cell earlier than the others. The
harm is worse on this side, because those lines are precisely the headwords:
« protezo » read « rotezo », « protisto » « rotisto », « sorgumo » « orgumo ».

We do not re-cut the book for all that -- widening the block means re-cutting
everything, which had lost headwords on a hundred and forty-five pages. We
therefore re-cut each page IN MEMORY with the block extended to the left,
attach the recovered cells to the group whose centre is nearest in the
features2 space, and deposit them apart. The recorded cutting does not move:
no correction already made is invalidated.

The difference from the right-hand side lies in the numbering. On the right,
the recovered cells take the columns that follow the block: nothing moves. On
the left, they fall BEFORE column zero. Renumbering them by shifting the one
line concerned would be wrong -- it would end up one cell to the right of its
real place. We therefore shift the WHOLE PAGE by as many cells as are missing:
the relative positions are kept to the character, and the block, whose margin
is fixed elsewhere, falls in the same place on the sheet. It is
generate.lignes_page() that applies that shift, shifting the underline ranges
with it.
"""
import sys, os, pickle, glob, re
import numpy as np
sys.path.insert(0, '/root/dicionario/outils')
import cells
from features2 import feature_vector2
ROOT = "/root/dicionario"; T = f"{ROOT}/travail"


def one_(pg, Q, tab):
    """Characters recovered left of the block: {line: {negative column: char}}."""
    z = np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    col0 = int(z['col0'])
    keys_ = set(int(k) for k, _ in z['lignes'])
    cells_of.ETENDRE = True; cells_of.ETENDRE_D = False; cells_of.ETENDRE_FORCE = 2
    try:
        d = cells_of.extract(f"{ROOT}/scan/p-{pg:03d}.jpg")
    finally:
        cells_of.ETENDRE = False; cells_of.ETENDRE_FORCE = 0
    lg = np.array(d['lignes'])
    if set(int(k) for k in lg[:, 0]) != keys_:
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
    edge = (P[:, :, :2].sum((1, 2)) + P[:, :, -2:].sum((1, 2))) / (tot + 1e-6)
    top = P[:, :4, :].sum((1, 2)) / (tot + 1e-6)
    bottom = P[:, 18:, :].sum((1, 2)) / (tot + 1e-6)
    smudge = ((edge > 0.55) | ((tot < 12) & (edge > 0.25)) | (top > 0.80) | (bottom > 0.85))
    X = feature_vector2(A); X = X / np.maximum(np.linalg.norm(X, axis=1, keepdims=True), 1e-6)
    g = (X @ Q.T).argmax(1)
    out = {}
    for i in range(len(ii)):
        if smudge[i]:
            continue
        ch = str(tab[g[i]])
        if ch == ' ' or len(ch) != 1:
            continue
        out.setdefault(int(lg[ii[i], 0]), {})[int(jj[i]) - delta] = ch
    return out, None


def all_(out_path=f"{T}/debuts.pkl", start_=0, end_=None):
    Q = np.load(f"{T}/km_centres2.npy")
    tab = np.load(f"{T}/cls_lab.npy", allow_pickle=True)
    pages = sorted(int(re.search(r'p-(\d+)', f).group(1))
                   for f in glob.glob(f"{T}/cellules/p-*.npz"))
    pages = [p for p in pages if p >= start_ and (end_ is None or p < end_)]
    out = {}; refused = 0
    for i, pg in enumerate(pages):
        try:
            r, err = one_(pg, Q, tab)
        except Exception as e:
            print("ECHEC p%03d : %s" % (pg, e), flush=True); continue
        if r is None:
            refused += 1
        elif r:
            out[pg] = r
            print("  p%03d : %s" % (pg, sorted((k, "".join(v[c] for c in sorted(v)))
                                               for k, v in r.items())), flush=True)
        if i % 50 == 0:
            print("  ...%d/%d" % (i, len(pages)), flush=True)
    with open(out_path, "wb") as f:
        pickle.dump(out, f)
    print("pages with a start recovered: %d ; pages refused: %d" % (len(out), refused))
    return out


if __name__ == "__main__":
    all_()
