"""Realigns the seed transcriptions after a change in line numbering."""
import numpy as np, glob, os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"
def motif(s, n): return "".join("#" if c!=" " else "." for c in s).ljust(n,".")[:n]
def recaler(f):
    pg=int(os.path.basename(f)[1:4])
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    occ=z['occ']; lg=z['lignes']
    ref={int(k):"".join("#" if o else "." for o in occ[i]) for i,k in enumerate(lg[:,0])}
    lines=[]
    for l in open(f, encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip(): continue
        k,_,s=l.partition("\t"); lines.append((int(k), s))
    best=None
    for dk in range(-6,7):
        sc=0; nb=0
        for k,s in lines:
            m=ref.get(k+dk)
            if m is None: continue
            t=motif(s,len(m)); nb+=1
            sc+=sum(1 for a,b in zip(t,m) if a=="#" and b==".")
        if nb==len(lines) and (best is None or sc<best[0]): best=(sc,dk)
    if best is None: return None
    sc,dk=best
    if dk:
        open(f,"w",encoding='utf-8').write("\n".join(f"{k+dk}\t{s}" for k,s in lines)+"\n")
    return dk, sc
if __name__=="__main__":
    for f in sorted(glob.glob(f"{T}/amorce/p*.txt")):
        print(os.path.basename(f), recaler(f))
