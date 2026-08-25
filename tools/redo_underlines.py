"""Recomputes the underline survey alone and re-injects it into the .npz,
without touching the cells or their labelling."""
import sys, os, glob, numpy as np, pickle
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from multiprocessing import Pool
from page import analyse
from cells import underlines, raffiner_pas
T=_ROOT + "/work"
def un(n):
    try:
        z=dict(np.load(f"{T}/cellules/{n}.npz", allow_pickle=True))
        d=analyse(f_ROOT + "/scan/{n}.jpg")
        hstep, xg = raffiner_pas(d['norm'], d['bloc'], d['pash'], d['xg'])
        xg = xg % hstep
        ncol=int(np.floor((d['norm'].shape[1]-xg)/hstep))
        underline=underlines(d['norm'], d['lignes'], d['pasv'], hstep, xg, ncol)
        c0=int(z['col0'])
        underline={k:(rr,[(a-c0,b-c0) for a,b in pl],t) for k,(rr,pl,t) in underline.items()}
        z['sou']=np.array(pickle.dumps(underline), dtype=object)
        np.savez_compressed(f"{T}/cellules/{n}.npz", **z)
        return n,"ok"
    except Exception as e:
        return n, f"ERR {type(e).__name__}: {e}"
if __name__=="__main__":
    names=[os.path.basename(p)[:-4] for p in sorted(glob.glob(f"{T}/cellules/*.npz"))]
    with Pool(2) as p:
        for i,(n,s) in enumerate(p.imap_unordered(un, names, chunksize=4)):
            if s.startswith("ERR") or i%100==0: print(i,n,s, flush=True)
