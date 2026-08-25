"""Analyse d'une page : desinclinaison, lattis des lignes, lattis des colonnes."""
import numpy as np
from PIL import Image
from scipy.ndimage import rotate as ndrotate, uniform_filter, gaussian_filter1d

PASV_NOM = 17.85   # pas vertical nominal (px @150dpi)
PASH_NOM = 10.55   # pas horizontal nominal

def charger(p):
    return np.asarray(Image.open(p).convert("L")).astype(np.float32)

def normaliser(a, w=41):
    fond = uniform_filter(a, size=w)
    d = np.clip(fond - a, 0, None)
    m = np.percentile(d, 99.7)
    return np.clip(d / (m if m > 1 else 1), 0, 1)

def masquer_bords(b, seuil=0.18, frac=0.45, marge=0.16):
    """Efface les bandes sombres collees aux bords de l'image : ce sont les
    ombres du bord du papier ou de la reliure, pas du texte. Le seuil est bas
    a dessein : ces ombres sont grises, pas noires."""
    H, W = b.shape
    colonne = (b > seuil).mean(axis=0)
    ligne   = (b > seuil).mean(axis=1)
    # L'ombre du bord n'est pas toujours collee au bord de l'image : le cadrage
    # laisse souvent quelques millimetres de blanc avant elle. On cherche donc
    # la derniere bande sombre dans la marge, et on efface tout jusqu'a elle.
    lim = int(W*marge); limh = int(H*marge)

    def _bande(prof, bord_max, trou_max):
        """Longueur de la bande sombre issue du bord.

        La version precedente prenait la DERNIERE rangee sombre de la marge et
        effacait tout jusqu'a elle. Une ligne de texte soulignee est sombre :
        sur la page 28, une ligne a la rangee 177 etait prise pour une ombre et
        le masque detruisait six lignes de texte. Une ombre de bord, elle,
        touche le bord et reste continue ; une ligne soulignee est isolee au
        milieu du blanc. On exige donc la continuite depuis le bord."""
        fin = -1; trou = 0
        for i, v in enumerate(prof):
            if v > frac:
                fin = i; trou = 0
            else:
                if fin >= 0:
                    trou += 1
                    if trou > trou_max: break
                elif i > bord_max: break
        return fin

    # La continuite depuis le bord ne vaut que dans le sens des LIGNES.
    # Une ligne de texte soulignee peut etre sombre sur 45 % de la largeur ;
    # une colonne de caracteres, jamais sur 45 % de la hauteur. Cote gauche et
    # droit, l'ancienne regle — la derniere colonne sombre de la marge — reste
    # donc la bonne : l'assouplir laisse l'ombre de reliure dans l'image, et le
    # lattis de colonnes s'accroche dessus. Essaye : soixante pages y ont perdu
    # toutes leurs vedettes, le texte revenant entrelace.
    by = int(H*0.02); ty = int(H*0.012)
    sombres = np.where(colonne[:lim] > frac)[0]
    g = int(sombres.max())+6 if len(sombres) else 0
    sombres = np.where(colonne[W-lim:] > frac)[0]
    d = (W-lim+int(sombres.min())-5) if len(sombres) else W-1
    f = _bande(ligne[:limh], by, ty);             h = f+6 if f >= 0 else 0
    f = _bande(ligne[::-1][:limh], by, ty);       bas = (H-1-f-5) if f >= 0 else H-1
    if g: b[:, :g+1] = 0
    if d < W-1: b[:, d:] = 0
    if h: b[:h+1, :] = 0
    if bas < H-1: b[bas:, :] = 0
    return b

def _score(b, ang):
    r = ndrotate(b, ang, reshape=False, order=1, mode='constant', cval=0)
    return np.diff(r.sum(axis=1)).var()

def desincliner(b, plage=2.5):
    gs = np.arange(-plage, plage+1e-9, 0.25)
    a0 = max(gs, key=lambda a: _score(b, a))
    fs = np.arange(a0-0.25, a0+0.25+1e-9, 0.05)
    a1 = max(fs, key=lambda a: _score(b, a))
    return a1, ndrotate(b, a1, reshape=False, order=1, mode='constant', cval=0)

def dft_pas(prof, lo, hi, n=1201):
    x = np.arange(len(prof)); s = prof - prof.mean()
    best = (-1, lo, 0.)
    for p in np.linspace(lo, hi, n):
        w = 2*np.pi/p
        c = (s*np.cos(w*x)).sum(); d = (s*np.sin(w*x)).sum()
        m = np.hypot(c, d)
        if m > best[0]: best = (m, p, np.arctan2(d, c))
    m, p, ph = best
    x_max = (ph*p/(2*np.pi)) % p      # position de max d'encre modulo p
    return p, x_max, m/(np.abs(s).sum()+1e-9)

def bloc_texte(r, seuil=0.06):
    ph = r.sum(axis=1)
    ys = np.where(ph > ph.max()*seuil)[0]
    pv = r[ys.min():ys.max()+1].sum(axis=0)
    xs = np.where(pv > pv.max()*0.04)[0]
    return ys.min(), ys.max(), xs.min(), xs.max()

def lattis_lignes(r, y0, y1, pas_nom=PASV_NOM):
    """Lattis vertical : pas + phase par Fourier, puis affinage local par ligne."""
    ph = gaussian_filter1d(r.sum(axis=1), 1.0)
    seg = ph[y0:y1+1]
    pas, ymax, q = dft_pas(seg, pas_nom*0.93, pas_nom*1.07, 801)
    n = int(np.floor((len(seg)-1-ymax)/pas)) + 1
    ks = np.arange(n)
    ys = ymax + ks*pas
    seuil = max(seg.max()*0.06, 2.0)
    # affinage : pour chaque ligne occupee, barycentre local sur +-pas/2
    obs_k, obs_y = [], []
    for k, y in zip(ks, ys):
        i0 = int(round(y-pas*0.42)); i1 = int(round(y+pas*0.42))
        i0 = max(i0,0); i1 = min(i1, len(seg))
        if i1-i0 < 3: continue
        w = seg[i0:i1]
        if w.sum() > seuil*(i1-i0)*0.8 and w.max() > seuil:
            c = i0 + (w*np.arange(len(w))).sum()/w.sum()
            obs_k.append(k); obs_y.append(c)
    if len(obs_k) >= 4:
        A = np.vstack([np.array(obs_k, float), np.ones(len(obs_k))]).T
        sol, *_ = np.linalg.lstsq(A, np.array(obs_y), rcond=None)
        res = np.abs(A@sol - np.array(obs_y))
        keep = res < pas*0.30
        if keep.sum() >= 4:
            sol, *_ = np.linalg.lstsq(A[keep], np.array(obs_y)[keep], rcond=None)
        pas, ymax = float(sol[0]), float(sol[1])
        n = int(np.floor((len(seg)-1-ymax)/pas)) + 1
        ks = np.arange(max(n,0))
        ys = ymax + ks*pas
    # le lattis est prolonge a toute la hauteur de l'image : les folios et les
    # lignes isolees hors du bloc principal (titres, notes) doivent etre pris.
    tot = ph
    seuil2 = max(seg.max()*0.02, 3.0)   # hors du bloc principal : folios, notes
    k0 = int(np.floor((0 - (ymax+y0))/pas))
    k1 = int(np.ceil((len(tot)-1 - (ymax+y0))/pas))
    occupe = []
    for k in range(k0, k1+1):
        y = ymax + y0 + k*pas
        i0 = max(int(round(y-pas*0.45)),0); i1 = min(int(round(y+pas*0.45)), len(tot))
        if i1-i0 < 3: continue
        dans = (y0 <= y <= y1)
        if tot[i0:i1].max() > (seuil if dans else seuil2):
            occupe.append((int(k), float(y)))
    if occupe:
        d0 = occupe[0][0]
        occupe = [(k-d0, y) for k,y in occupe]
    return pas, occupe, ph

def lattis_colonnes(r, y0, y1, x0, x1, pas_nom=PASH_NOM):
    pv = r[y0:y1+1, x0:x1+1].sum(axis=0)
    pas, xmax, q = dft_pas(pv, pas_nom*0.94, pas_nom*1.06, 1201)
    # bord gauche de cellule : encre centree sur xmax -> bord a xmax - pas/2
    xg = (xmax - pas/2) % pas
    return pas, x0 + xg, q

RAPPORT = 1.700   # pas vertical / pas horizontal, mesure sur l'ensemble du livre

HAUT_NOM = 1119.0   # hauteur mediane des images de page

def echelle(a):
    """Deux pages du scan (538 et 539) sont photographiees a 1,47x. On deduit
    l'echelle de la hauteur de l'image : toutes les autres sont a 1,0x."""
    h = a.shape[0]
    return 1.0 if h < 1300 else h/HAUT_NOM

def _analyser_brut(a):
    b = masquer_bords(normaliser(a))
    ang, r = desincliner(b)
    y0, y1, x0, x1 = bloc_texte(r)
    pasv, lignes, ph = lattis_lignes(r, y0, y1, pas_nom=PASV_NOM)
    pash, xg, q = lattis_colonnes(r, y0, y1, x0, x1, pas_nom=PASH_NOM)
    return dict(img=a, norm=r, angle=ang, bloc=(y0,y1,x0,x1),
                pasv=pasv, lignes=lignes, pash=pash, xg=xg, q=q)

def analyser(chemin):
    a = charger(chemin)
    # Deux pages du scan sont photographiees a 1,47x. On les ramene a l'echelle
    # commune des 637 autres : sinon leurs cellules, rechantillonnees depuis une
    # image plus fine, ne ressemblent a aucune des autres et forment des groupes
    # a part, sans etiquette.
    e = echelle(a)
    if abs(e-1.0) > 0.05:
        a = _redim(a, e)
    d = _analyser_brut(a)
    # affinage : si la chasse mesuree s'ecarte de la norme de plus de 3 %, la
    # page a ete photographiee a une autre distance ; on la ramene a l'echelle
    # commune et on recommence. Les cellules doivent etre comparables d'une
    # page a l'autre, sinon le regroupement les separe pour rien.
    for _ in range(6):
        f = d['pash']/PASH_NOM
        if abs(f-1.0) <= 0.012: break
        a = _redim(a, f)
        d = _analyser_brut(a)
    return d

def _redim(a, f):
    from PIL import Image as _I
    im=_I.fromarray(np.clip(a,0,255).astype(np.uint8))
    return np.asarray(im.resize((max(int(round(a.shape[1]/f)),1),
                                 max(int(round(a.shape[0]/f)),1)),
                                _I.LANCZOS)).astype(np.float32)
