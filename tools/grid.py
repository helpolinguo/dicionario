"""Measuring a typescript's grid: deskewing, vertical pitch, horizontal pitch."""
import numpy as np, sys
from PIL import Image
from scipy.ndimage import rotate as ndrotate, uniform_filter

def charger(p):
    im = Image.open(p).convert("L")
    a = np.asarray(im).astype(np.float32)
    return a

def normaliser(a, w=41):
    """Local contrast: ground = wide mean filter, ink = negative departure."""
    fond = uniform_filter(a, size=w)
    d = fond - a                      # ink > 0
    d = np.clip(d, 0, None)
    m = np.percentile(d, 99.7)
    if m <= 1: m = 1
    return np.clip(d / m, 0, 1)

def score_angle(b, ang):
    r = ndrotate(b, ang, reshape=False, order=1, mode='constant', cval=0)
    prof = r.sum(axis=1)
    return prof.var(), prof

def desincliner(b, plage=3.0, pas=0.05):
    grossier = np.arange(-plage, plage+1e-9, 0.25)
    sc = [(score_angle(b,a)[0], a) for a in grossier]
    _, a0 = max(sc)
    fin = np.arange(a0-0.25, a0+0.25+1e-9, pas)
    sc = [(score_angle(b,a)[0], a) for a in fin]
    _, a1 = max(sc)
    return a1, ndrotate(b, a1, reshape=False, order=1, mode='constant', cval=0)

def pas_par_autocorr(prof, lo, hi):
    """Dominant pitch of a profile by autocorrelation, with parabolic interpolation."""
    x = prof - prof.mean()
    ac = np.correlate(x, x, mode='full')[len(x)-1:]
    ac = ac / (ac[0] + 1e-9)
    seg = ac[lo:hi]
    k = int(np.argmax(seg)) + lo
    if 0 < k < len(ac)-1:
        y0,y1,y2 = ac[k-1],ac[k],ac[k+1]
        d = (y0 - y2) / (2*(y0 - 2*y1 + y2) + 1e-12)
        return k + d, ac[k]
    return float(k), ac[k]

if __name__ == "__main__":
    for p in sys.argv[1:]:
        a = charger(p); b = normaliser(a)
        ang, r = desincliner(b)
        ph = r.sum(axis=1)   # horizontal profile (lines)
        pv = r.sum(axis=0)   # vertical profile (columns)
        pvY, cy = pas_par_autocorr(ph, 12, 60)
        pvX, cx = pas_par_autocorr(pv, 6, 40)
        enc = (r>0.25).sum()
        print(f"{p}: {a.shape[1]}x{a.shape[0]} angle={ang:+.2f} pasV={pvY:.3f}px ({150/pvY:.2f} lpi, r={cy:.2f})  pasH={pvX:.3f}px ({150/pvX:.2f} cpi, r={cx:.2f}) encre={enc}")
