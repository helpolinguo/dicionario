# -*- coding: utf-8 -*-
"""Restitution du mot « invitas » sur la couverture.

Dans le scan, ce mot est presque efface : « inv » subsiste, puis « as », et
entre les deux le papier est nu — le niveau d'encre y plafonne a 0,146 et le
95e centile a 0,014. Aucun seuil ne fera apparaitre ce qui n'a pas ete
imprime. Ne restent, dans l'intervalle, que trois salissures.

On ne dessine pourtant rien. Les deux lettres manquantes, un « i » et un
« t », figurent a quelques centimetres de la, dans « profitar » — meme ligne,
meme main, meme corps, et dans le meme ordre. On les y prend, on les tourne de
la difference d'inclinaison entre les deux endroits de l'arc, et on les repose
a la place que l'espacement de « profitar » leur assigne. Chaque trait de la
couverture reste donc de la couverture.

Le choix des composantes s'est fait a l'oeil, sur planche (work/cv_zone.png
et work/cv_inv.png). On les designe ici par leur numero d'etiquette, mais on
verifie leur signature (centre, surface) avant de s'en servir : si la
binarisation change, le script s'arrete au lieu de transplanter n'importe quoi.
Une premiere version choisissait la composante « la plus proche d'un point » ;
elle est allee prendre un « o » et a ecrit « invoias ».
"""
import numpy as np, sys
sys.path.insert(0, '/root/dicionario/outils')
from cover import binariser_trait, SUR
from scipy.ndimage import label, find_objects, rotate as ndrot

RAC = "/root/dicionario"

# Signatures relevees sur la trame x4, repere de l'image entiere :
#   etiquette : (cx, cy, surface)
SRC_I  = (509, 1566, 1860,  588)   # le « i » de profitar
SRC_T  = (502, 1589, 1855,  832)   # le « t » de profitar
SRC_F  = (501, 1536, 1858,  941)   # le « f » de profitar (repere gauche)
SRC_A  = (510, 1628, 1858, 1175)   # le « a » de profitar (repere droit)

CIB_V  = (557, 1053, 1982,  619)   # le « v » de invitas (repere gauche)
CIB_A  = (547, 1163, 1953, 1330)   # le « a » de invitas (repere droit)
CIB_I  = (558,  978, 2003,  661)   # le « i » de invitas : donne l'inclinaison

DEBRIS = [(554, 1088, 1969, 175), (550, 1122, 1946, 123), (556, 1125, 1974, 295)]

TOL_POS, TOL_AIRE = 6, 0.15        # tolerance de verification


def _prendre(l, obj, sig):
    """Composante retrouvee par sa signature : centre et surface.

    On ne se fie pas au numero d'etiquette — il change des que la binarisation
    bouge. On cherche donc, parmi toutes les composantes, celle dont le centre
    et la surface repondent a la signature relevee sur planche. S'il n'y en a
    pas exactement une, on s'arrete : mieux vaut un script qui refuse de
    tourner qu'une greffe posee au mauvais endroit.
    """
    _, cx, cy, aire = sig
    cands = []
    for i, o in enumerate(obj):
        if o is None:
            continue
        ccy = (o[0].start + o[0].stop) // 2
        ccx = (o[1].start + o[1].stop) // 2
        if abs(ccx - cx) > TOL_POS or abs(ccy - cy) > TOL_POS:
            continue
        a = int((l[o] == i + 1).sum())
        if abs(a - aire) > TOL_AIRE * aire:
            continue
        cands.append((i + 1, o))
    if len(cands) != 1:
        raise SystemExit(
            "signature (%d,%d,aire %d) : %d composantes candidates au lieu d'une.\n"
            "La binarisation a bouge : refaire les planches avant de continuer."
            % (cx, cy, aire, len(cands)))
    return cands[0]


def _angle(a, b):
    return np.degrees(np.arctan2(b[2] - a[2], b[1] - a[1]))


def _axe(l, k, o):
    """Inclinaison du fut d'une lettre, par son axe principal (degres, 0-180)."""
    ys, xs = np.nonzero(l[o] == k)
    ys = ys.astype(float) - ys.mean(); xs = xs.astype(float) - xs.mean()
    w, v = np.linalg.eigh(np.cov(np.vstack([xs, ys])))
    a = np.degrees(np.arctan2(v[1, -1], v[0, -1]))
    return a + 180 if a < 0 else a


def appliquer(B):
    """Repare le mot en place sur un calque de trait deja binarise."""
    l, nb = label(B, np.ones((3, 3), int))
    obj = find_objects(l)

    # 1. effacer les trois salissures de l'intervalle
    for sig in DEBRIS:
        k, o = _prendre(l, obj, sig)
        B[o] &= ~(l[o] == k)

    # 2. inclinaison a donner aux lettres.
    #
    # Premiere version : la difference des angles de corde entre les deux
    # endroits de l'arc. C'etait faux deux fois — de valeur (la corde n'est pas
    # l'inclinaison des lettres, qui se redressent sur l'arc) et de signe
    # (ndimage.rotate tourne dans le sens oppose a celui suppose). Les lettres
    # penchaient a droite au lieu de pencher a gauche.
    #
    # On mesure donc directement, sur la meme lettre : l'axe principal du « i »
    # de profitar et celui du « i » de invitas, quatre lettres plus tot. Leur
    # difference est exactement ce qu'il faut tourner, signe compris.
    ki, oi = _prendre(l, obj, SRC_I)
    kc, oc = _prendre(l, obj, CIB_I)
    da = _axe(l, ki, oi) - _axe(l, kc, oc)

    # 3. positions : l'espacement de « profitar », mis a l'echelle de l'ecart
    #    disponible. f->i et f->t donnent les deux abscisses ; l'ecart vertical
    #    de chaque lettre a la corde f-a est reporte tel quel.
    port_s = SRC_A[1] - SRC_F[1]
    port_c = CIB_A[1] - CIB_V[1]
    ech = port_c / float(port_s)
    cibles = []
    for src in (SRC_I, SRC_T):
        f = (src[1] - SRC_F[1]) / float(port_s)          # position relative
        dy = src[2] - (SRC_F[2] + f * (SRC_A[2] - SRC_F[2]))   # ecart a la corde
        x = CIB_V[1] + f * port_c
        y = CIB_V[2] + f * (CIB_A[2] - CIB_V[2]) + dy
        cibles.append((x, y))

    # 4. prendre, tourner, reposer
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
          % (da, ech, cibles[0][0], cibles[0][1], cibles[1][0], cibles[1][1]))
    return B


def executer(sortie=f"{RAC}/work/couv/B_repare.npy"):
    n = np.load(f"{RAC}/work/couv/niveaux.npy")
    B = appliquer(binariser_trait(n))
    np.save(sortie, B)
    return B


if __name__ == "__main__":
    executer()
