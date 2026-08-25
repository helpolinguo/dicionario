import sys, os, numpy as np, pickle, glob
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from cells import extract
from multiprocessing import Pool
SCAN=_ROOT + "/scan"; OUT=_ROOT + "/work/cells"
os.makedirs(OUT, exist_ok=True)
def un(n):
    dst=f"{OUT}/{n}.npz"
    if os.path.exists(dst): return n,"deja"
    try:
        d=extract(f"{SCAN}/{n}.jpg")
        c=(np.clip(d['cells'],0,1)*255).astype(np.uint8)
        np.savez_compressed(dst, cells=c, nues=(np.clip(d['nues'],0,1)*255).astype(np.uint8), occ=d['occ'],
            lignes=np.array(d['lignes']), pasv=d['pasv'], pash=d['pash'],
            xg=d['xg'], col0=d['col0'], angle=d['angle'], bloc=np.array(d['bloc']),
            shape=np.array(d['shape']),
            sou=np.array(pickle.dumps(d['sou']), dtype=object))
        return n,"ok"
    except Exception as e:
        return n, f"ERR {type(e).__name__}: {e}"
if __name__=="__main__":
    names=sys.argv[1:]
    if not names: names=[os.path.basename(p)[:-4] for p in sorted(glob.glob(SCAN+"/*.jpg"))]
    with Pool(2) as pool:
        for i,(n,s) in enumerate(pool.imap_unordered(un, names, chunksize=4)):
            if s.startswith("ERR") or i%50==0: print(i,n,s, flush=True)
