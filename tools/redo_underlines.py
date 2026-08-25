"""Recomputes the underline survey alone and re-injects it into the .npz,
without touching the cells or their labelling."""
import sys, os, glob, numpy as np, pickle
sys.path.insert(0,'/root/dicionario/outils')
from multiprocessing import Pool
from page import analyser
from cells import soulignements, raffiner_pas
T="/root/dicionario/travail"
def un(n):
    try:
        z=dict(np.load(f"{T}/cellules/{n}.npz", allow_pickle=True))
        d=analyser(f"/root/dicionario/scan/{n}.jpg")
        pash, xg = raffiner_pas(d['norm'], d['bloc'], d['pash'], d['xg'])
        xg = xg % pash
        ncol=int(np.floor((d['norm'].shape[1]-xg)/pash))
        sou=soulignements(d['norm'], d['lignes'], d['pasv'], pash, xg, ncol)
        c0=int(z['col0'])
        sou={k:(rr,[(a-c0,b-c0) for a,b in pl],t) for k,(rr,pl,t) in sou.items()}
        z['sou']=np.array(pickle.dumps(sou), dtype=object)
        np.savez_compressed(f"{T}/cellules/{n}.npz", **z)
        return n,"ok"
    except Exception as e:
        return n, f"ERR {type(e).__name__}: {e}"
if __name__=="__main__":
    noms=[os.path.basename(p)[:-4] for p in sorted(glob.glob(f"{T}/cellules/*.npz"))]
    with Pool(2) as p:
        for i,(n,s) in enumerate(p.imap_unordered(un, noms, chunksize=4)):
            if s.startswith("ERR") or i%100==0: print(i,n,s, flush=True)
