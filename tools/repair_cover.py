# -*- coding: utf-8 -*-
"""Restoring the word « invitas » on the cover.

In the scan, that word is almost erased: « inv » survives, then « as », and
between the two the paper is bare -- the ink level there peaks at 0.146 and
the 95th percentile at 0.014. No threshold will bring out what was not
printed. All that remains in the gap is three smuts.

We draw nothing, all the same. The two missing letters, an « i » and a « t »,
appear a few centimetres away, in « profitar » -- same line, same hand, same
size, and in the same order. We take them from there, turn them by the
difference of inclination between the two places on the arc, and lay them back
in the place the spacing of « profitar » assigns them. Every stroke of the
cover therefore remains the cover's own.

The choice of components was made by eye, on a sheet (work/cv_zone.png and
work/cv_inv.png). We designate them here by their label number, but we verify
their signature (centre, area) before using them: if the binarisation changes,
the script stops instead of transplanting anything at all. A first version
chose the component « nearest to a point »; it went and took an « o » and
wrote « invoias ».
"""
import numpy as np, sys
sys.path.insert(0, '/root/dicionario/outils')
from cover import binariser_trait, SUR
from scipy.ndimage import label, find_objects, rotate as ndrot

ROOT = "/root/dicionario"

# Signatures surveyed on the x4 screen, in the frame of the whole image:
#   label: (cx, cy, area)
SRC_I  = (509, 1566, 1860,  588)   # the « i » of profitar
SRC_T  = (502, 1589, 1855,  832)   # the « t » of profitar
SRC_F  = (501, 1536, 1858,  941)   # the « f » of profitar (left cue)
SRC_A  = (510, 1628, 1858, 1175)   # the « a » of profitar (right cue)

CIB_V  = (557, 1053, 1982,  619)   # the « v » of invitas (left cue)
CIB_A  = (547, 1163, 1953, 1330)   # the « a » of invitas (right cue)
CIB_I  = (558,  978, 2003,  661)   # the « i » of invitas: gives the inclination

DEBRIS = [(554, 1088, 1969, 175), (550, 1122, 1946, 123), (556, 1125, 1974, 295)]

TOL_POS, TOL_AIRE = 6, 0.15        # tolerance of the verification


def _prendre(l, obj, sig):
    """A component found again by its signature: centre and area.

    We do not trust the label number -- it changes as soon as the binarisation
    moves. We therefore look, among all the components, for the one whose
    centre and area answer the signature surveyed on the sheet. If there is
    not exactly one, we stop: better a script that refuses to run than a graft
    laid in the wrong place.
    """
    _, cx, cy, area = sig
    cands = []
    for i, o in enumerate(obj):
        if o is None:
            continue
        ccy = (o[0].start + o[0].stop) // 2
        ccx = (o[1].start + o[1].stop) // 2
        if abs(ccx - cx) > TOL_POS or abs(ccy - cy) > TOL_POS:
            continue
        a = int((l[o] == i + 1).sum())
        if abs(a - area) > TOL_AIRE * area:
            continue
        cands.append((i + 1, o))
    if len(cands) != 1:
        raise SystemExit(
            "signature (%d,%d,aire %d) : %d composantes candidates au lieu d'une.\n"
            "La binarisation a bouge : refaire les planches avant de continuer."
            % (cx, cy, area, len(cands)))
    return cands[0]


def _angle(a, b):
    return np.degrees(np.arctan2(b[2] - a[2], b[1] - a[1]))


def _axe(l, k, o):
    """Inclination of a letter's stem, by its principal axis (degrees, 0-180)."""
    ys, xs = np.nonzero(l[o] == k)
    ys = ys.astype(float) - ys.mean(); xs = xs.astype(float) - xs.mean()
    w, v = np.linalg.eigh(np.cov(np.vstack([xs, ys])))
    a = np.degrees(np.arctan2(v[1, -1], v[0, -1]))
    return a + 180 if a < 0 else a


def apply_(B):
    """Repairs the word in place on an already binarised line layer."""
    l, nb = label(B, np.ones((3, 3), int))
    obj = find_objects(l)

    # 1. erase the three smuts in the gap
    for sig in DEBRIS:
        k, o = _prendre(l, obj, sig)
        B[o] &= ~(l[o] == k)

    # 2. the inclination to give the letters.
    #
    # First version: the difference of the chord angles between the two places
    # on the arc. That was wrong twice over -- in value (the chord is not the
    # inclination of the letters, which straighten along the arc) and in sign
    # (ndimage.rotate turns the opposite way to the one supposed). The letters
    # leaned right instead of leaning left.
    #
    # We therefore measure directly, on the same letter: the principal axis of
    # the « i » of profitar and that of the « i » of invitas, four letters
    # earlier. Their difference is exactly what must be turned, sign included.
    ki, oi = _prendre(l, obj, SRC_I)
    kc, oc = _prendre(l, obj, CIB_I)
    da = _axe(l, ki, oi) - _axe(l, kc, oc)

    # 3. positions: the spacing of « profitar », brought to the scale of the
    #    gap available. f->i and f->t give the two abscissae; each letter's
    #    vertical departure from the chord f-a is carried over as it stands.
    port_s = SRC_A[1] - SRC_F[1]
    port_c = CIB_A[1] - CIB_V[1]
    scale = port_c / float(port_s)
    cibles = []
    for src in (SRC_I, SRC_T):
        f = (src[1] - SRC_F[1]) / float(port_s)          # relative position
        dy = src[2] - (SRC_F[2] + f * (SRC_A[2] - SRC_F[2]))   # departure from the chord
        x = CIB_V[1] + f * port_c
        y = CIB_V[2] + f * (CIB_A[2] - CIB_V[2]) + dy
        cibles.append((x, y))

    # 4. take, turn, lay back
    for src, (cx, cy) in zip((SRC_I, SRC_T), cibles):
        k, o = _prendre(l, obj, src)
        g = (l[o] == k)
        g = ndrot(g.astype(np.float32), da, order=1, reshape=True, cval=0.0) > 0.5
        h, w = g.shape
        y0 = int(round(cy - h / 2.0)); x0 = int(round(cx - w / 2.0))
        sl = (slice(max(y0, 0), min(y0 + h, B.shape[0])),
              slice(max(x0, 0), min(x0 + w, B.shape[1])))
        B[sl] |= g[:sl[0].stop - sl[0].start, :sl[1].stop - sl[1].start]

    print("  invitas : angle %+.1f deg, echelle d'espacement %.3f ; "
          "i en (%.0f,%.0f), t en (%.0f,%.0f)"
          % (da, scale, cibles[0][0], cibles[0][1], cibles[1][0], cibles[1][1]))
    return B


def run_step(out_path=f"{ROOT}/work/couv/B_repare.npy"):
    n = np.load(f"{ROOT}/work/couv/niveaux.npy")
    B = apply_(binariser_trait(n))
    np.save(out_path, B)
    return B


if __name__ == "__main__":
    run_step()
