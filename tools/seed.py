"""Building a hand-labelled set: one verified transcription per page."""
import numpy as np, glob, os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T=_ROOT + "/work"
def read_(file_):
    d={}
    for l in open(file_, encoding='utf-8'):
        l=l.rstrip("\n")
        if not l or l.startswith("#"): continue
        k,_,s=l.partition("\t"); d[int(k)]=s
    return d
def pairs(pg, txt):
    """Returns (indices of cells in meta_all, characters)."""
    z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    occ=z['occ']; lg=z['lignes']
    M=np.load(f"{T}/meta_all.npy")
    sel=np.where(M[:,0]==pg)[0]
    pos={(int(k),int(c)):i for i,(p,k,c) in zip(sel, M[sel])}
    ncol=occ.shape[1]
    idx=[]; char_=[]; missing_ones=[]
    for k,s in txt.items():
        s=s.ljust(ncol)
        for c in range(ncol):
            ch=s[c]
            if (k,c) not in pos:
                if ch!=" ": missing_ones.append((k,c,ch))
                continue
            # inked cell: either a character, or a smudge -> space class
            idx.append(pos[(k,c)]); char_.append(ch)
    return np.array(idx), np.array(char_, dtype=object), missing_ones
def everything(reps=(f"{T}/amorce", f"{T}/amorce_folios")):
    I=[];C=[];Mq=[]
    files_=[]
    for r in reps: files_ += sorted(glob.glob(r+"/p*.txt"))
    for f in files_:
        pg=int(os.path.basename(f)[1:4])
        i,c,mq=pairs(pg, read_(f))
        I.append(i); C.append(c); Mq+= [(pg,)+m for m in mq]
    return np.concatenate(I), np.concatenate(C), Mq
