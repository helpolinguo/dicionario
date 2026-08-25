import numpy as np
def pitch_dft(prof, lo=9.0, hi=12.0, n=2001):
    """Pitch and phase by maximising the modulus of the Fourier component."""
    x = np.arange(len(prof)); s = prof - prof.mean()
    best=None
    for p in np.linspace(lo,hi,n):
        w = 2*np.pi/p
        c = (s*np.cos(w*x)).sum(); d=(s*np.sin(w*x)).sum()
        m = np.hypot(c,d)
        if best is None or m>best[0]:
            best=(m,p,np.arctan2(d,c))
    m,p,ph = best
    # x0: position of the minimum of ink (gutter) nearest to 0
    # profile ~ A cos(wx - ph); maximum of ink at x = ph/w; gutter at +p/2
    x0 = (ph/(2*np.pi/p)) + p/2
    x0 = x0 % p
    return p, x0, m/ (np.abs(s).sum()+1e-9)
