"""Analysis of a page: deskewing, lattice of lines, lattice of columns."""
import numpy as np
from PIL import Image
from scipy.ndimage import rotate as ndrotate, uniform_filter, gaussian_filter1d

NOMINAL_VSTEP = 17.85   # nominal vertical pitch (px @150dpi)
NOMINAL_HSTEP = 10.55   # nominal horizontal pitch

def load_(p):
    return np.asarray(Image.open(p).convert("L")).astype(np.float32)

def normalise(a, w=41):
    ground = uniform_filter(a, size=w)
    d = np.clip(ground - a, 0, None)
    m = np.percentile(d, 99.7)
    return np.clip(d / (m if m > 1 else 1), 0, 1)

def mask_edges(b, threshold=0.18, frac=0.45, margin=0.16):
    """Erases the dark bands stuck to the edges of the image: they are the
    shadows of the paper's edge or of the binding, not text. The threshold is
    low on purpose: those shadows are grey, not black."""
    H, W = b.shape
    column = (b > threshold).mean(axis=0)
    line_   = (b > threshold).mean(axis=1)
    # The edge shadow is not always stuck to the edge of the image: the framing
    # often leaves a few millimetres of white before it. We therefore look for
    # the last dark band in the margin, and erase everything as far as it.
    lim = int(W*margin); limh = int(H*margin)

    def _bande(depth, edge_max, hole_max):
        """The length of the dark band running from the edge.

        The previous version took the LAST dark row of the margin and erased
        everything as far as it. An underlined line of text is dark: on page
        28, a line at row 177 was taken for a shadow and the mask destroyed
        six lines of text. An edge shadow, for its part, touches the edge and
        stays continuous; an underlined line is isolated in the middle of the
        white. We therefore require continuity from the edge."""
        end_ = -1; hole = 0
        for i, v in enumerate(depth):
            if v > frac:
                end_ = i; hole = 0
            else:
                if end_ >= 0:
                    hole += 1
                    if hole > hole_max: break
                elif i > edge_max: break
        return end_

    # Continuity from the edge holds only in the direction of the LINES.
    # An underlined line of text can be dark over 45 % of the width; a column
    # of characters, never over 45 % of the height. On the left and right side
    # the old rule -- the last dark column of the margin -- therefore remains
    # the right one: relaxing it leaves the binding shadow in the image, and the
    # lattice of columns catches on it. Tried: sixty pages lost every one of
    # their headwords, the text coming back interleaved.
    by = int(H*0.02); ty = int(H*0.012)
    dark = np.where(column[:lim] > frac)[0]
    g = int(dark.max())+6 if len(dark) else 0
    dark = np.where(column[W-lim:] > frac)[0]
    d = (W-lim+int(dark.min())-5) if len(dark) else W-1
    f = _bande(line_[:limh], by, ty);             h = f+6 if f >= 0 else 0
    f = _bande(line_[::-1][:limh], by, ty);       bottom = (H-1-f-5) if f >= 0 else H-1
    if g: b[:, :g+1] = 0
    if d < W-1: b[:, d:] = 0
    if h: b[:h+1, :] = 0
    if bottom < H-1: b[bottom:, :] = 0
    return b

def _score(b, angle_):
    r = ndrotate(b, angle_, reshape=False, order=1, mode='constant', cval=0)
    return np.diff(r.sum(axis=1)).var()

def deskew(b, range_=2.5):
    gs = np.arange(-range_, range_+1e-9, 0.25)
    a0 = max(gs, key=lambda a: _score(b, a))
    fs = np.arange(a0-0.25, a0+0.25+1e-9, 0.05)
    a1 = max(fs, key=lambda a: _score(b, a))
    return a1, ndrotate(b, a1, reshape=False, order=1, mode='constant', cval=0)

def dft_step(depth, lo, hi, n=1201):
    x = np.arange(len(depth)); s = depth - depth.mean()
    best = (-1, lo, 0.)
    for p in np.linspace(lo, hi, n):
        w = 2*np.pi/p
        c = (s*np.cos(w*x)).sum(); d = (s*np.sin(w*x)).sum()
        m = np.hypot(c, d)
        if m > best[0]: best = (m, p, np.arctan2(d, c))
    m, p, ph = best
    x_max = (ph*p/(2*np.pi)) % p      # position of the ink maximum modulo p
    return p, x_max, m/(np.abs(s).sum()+1e-9)

def text_block(r, threshold=0.06):
    ph = r.sum(axis=1)
    ys = np.where(ph > ph.max()*threshold)[0]
    pv = r[ys.min():ys.max()+1].sum(axis=0)
    xs = np.where(pv > pv.max()*0.04)[0]
    return ys.min(), ys.max(), xs.min(), xs.max()

def line_lattice(r, y0, y1, nominal_step=NOMINAL_VSTEP):
    """Vertical lattice: pitch + phase by Fourier, then local refinement by line."""
    ph = gaussian_filter1d(r.sum(axis=1), 1.0)
    seg = ph[y0:y1+1]
    step, ymax, q = dft_step(seg, nominal_step*0.93, nominal_step*1.07, 801)
    n = int(np.floor((len(seg)-1-ymax)/step)) + 1
    ks = np.arange(n)
    ys = ymax + ks*step
    threshold = max(seg.max()*0.06, 2.0)
    # refinement: for each occupied line, a local barycentre over +-pitch/2
    obs_k, obs_y = [], []
    for k, y in zip(ks, ys):
        i0 = int(round(y-step*0.42)); i1 = int(round(y+step*0.42))
        i0 = max(i0,0); i1 = min(i1, len(seg))
        if i1-i0 < 3: continue
        w = seg[i0:i1]
        if w.sum() > threshold*(i1-i0)*0.8 and w.max() > threshold:
            c = i0 + (w*np.arange(len(w))).sum()/w.sum()
            obs_k.append(k); obs_y.append(c)
    if len(obs_k) >= 4:
        A = np.vstack([np.array(obs_k, float), np.ones(len(obs_k))]).T
        floor_, *_ = np.linalg.lstsq(A, np.array(obs_y), rcond=None)
        res = np.abs(A@floor_ - np.array(obs_y))
        keep = res < step*0.30
        if keep.sum() >= 4:
            floor_, *_ = np.linalg.lstsq(A[keep], np.array(obs_y)[keep], rcond=None)
        step, ymax = float(floor_[0]), float(floor_[1])
        n = int(np.floor((len(seg)-1-ymax)/step)) + 1
        ks = np.arange(max(n,0))
        ys = ymax + ks*step
    # the lattice is extended to the whole height of the image: the folios and
    # the isolated lines outside the main block (titles, notes) must be caught.
    tot = ph
    threshold2 = max(seg.max()*0.02, 3.0)   # outside the main block: folios, notes
    k0 = int(np.floor((0 - (ymax+y0))/step))
    k1 = int(np.ceil((len(tot)-1 - (ymax+y0))/step))
    occupied = []
    for k in range(k0, k1+1):
        y = ymax + y0 + k*step
        i0 = max(int(round(y-step*0.45)),0); i1 = min(int(round(y+step*0.45)), len(tot))
        if i1-i0 < 3: continue
        within = (y0 <= y <= y1)
        if tot[i0:i1].max() > (threshold if within else threshold2):
            occupied.append((int(k), float(y)))
    if occupied:
        d0 = occupied[0][0]
        occupied = [(k-d0, y) for k,y in occupied]
    return step, occupied, ph

def column_lattice(r, y0, y1, x0, x1, nominal_step=NOMINAL_HSTEP):
    pv = r[y0:y1+1, x0:x1+1].sum(axis=0)
    step, xmax, q = dft_step(pv, nominal_step*0.94, nominal_step*1.06, 1201)
    # left edge of a cell: ink centred on xmax -> edge at xmax - pitch/2
    xg = (xmax - step/2) % step
    return step, x0 + xg, q

RATIO = 1.700   # vertical pitch / horizontal pitch, measured over the whole book

NOMINAL_TOP = 1119.0   # median height of the page images

def scale_(a):
    """Two pages of the scan (538 and 539) are photographed at 1.47x. We deduce
    the scale from the height of the image: all the others are at 1.0x."""
    h = a.shape[0]
    return 1.0 if h < 1300 else h/NOMINAL_TOP

def _analyse_raw(a):
    b = mask_edges(normalise(a))
    angle_, r = deskew(b)
    y0, y1, x0, x1 = text_block(r)
    vstep, lines, ph = line_lattice(r, y0, y1, nominal_step=NOMINAL_VSTEP)
    hstep, xg, q = column_lattice(r, y0, y1, x0, x1, nominal_step=NOMINAL_HSTEP)
    return dict(img=a, norm=r, angle=angle_, bloc=(y0,y1,x0,x1),
                pasv=vstep, lignes=lines, pash=hstep, xg=xg, q=q)

def analyse(path_):
    a = load_(path_)
    # Two pages of the scan are photographed at 1.47x. We bring them back to the
    # common scale of the other 637: otherwise their cells, resampled from a
    # finer image, resemble none of the others and form groups of their own,
    # with no label.
    e = scale_(a)
    if abs(e-1.0) > 0.05:
        a = _resize(a, e)
    d = _analyse_raw(a)
    # refinement: if the measured set departs from the norm by more than 3 %,
    # the page was photographed at another distance; we bring it back to the
    # common scale and begin again. The cells must be comparable from one page
    # to another, or the grouping separates them for nothing.
    for _ in range(6):
        f = d['pash']/NOMINAL_HSTEP
        if abs(f-1.0) <= 0.012: break
        a = _resize(a, f)
        d = _analyse_raw(a)
    return d

def _resize(a, f):
    from PIL import Image as _I
    im=_I.fromarray(np.clip(a,0,255).astype(np.uint8))
    return np.asarray(im.resize((max(int(round(a.shape[1]/f)),1),
                                 max(int(round(a.shape[0]/f)),1)),
                                _I.LANCZOS)).astype(np.float32)
