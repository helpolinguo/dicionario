# -*- coding: utf-8 -*-
"""Where do the lines the block left outside fall on the page's lattice?

A page's lattice is a straight line: y(k) = y0 + k*pasv, where y0 is the
first STORED line, of index 0. A line lost above therefore takes a negative
index, a line lost below an index beyond the last. In this way the numbering
of the lines already read does not move, and no correction indexed by (page,
line, column) is invalidated.
"""
import sys, numpy as np
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
import page as P
ROOT=_ROOT; T=f"{ROOT}/work"

def lattice(pg, threshold=0.02):
    z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    lg=np.array(z['lignes']); vstep=float(z['pasv'])
    a=P.load_(f"{ROOT}/scan/p-{pg:03d}.jpg")
    b=P.mask_edges(P.normalise(a)); _,r=P.deskew(b)
    ph=r.sum(axis=1)
    y0=float(lg[0,1]); k0=int(lg[0,0])
    known_={int(k) for k in lg[:,0]}
    H=len(ph)
    kmin=int(np.floor((0-y0)/vstep))-1; kmax=int(np.ceil((H-1-y0)/vstep))+1
    vthreshold=max(ph.max()*threshold, 3.0)
    out=[]
    for k in range(kmin, kmax+1):
        y=y0+(k-k0)*vstep
        i0=max(int(round(y-0.45*vstep)),0); i1=min(int(round(y+0.45*vstep)),H)
        if i1-i0<3: continue
        ink_=float(ph[i0:i1].max())
        out.append((k, round(y,1), round(ink_,1), ink_>vthreshold, k in known_))
    return z, out

if __name__=="__main__":
    for pg in [int(x) for x in sys.argv[1:]]:
        z,out=lattice(pg)
        print("=== p%03d  vstep %.2f  block %s  %d lines stored"%(pg,float(z['pasv']),list(z['bloc']),len(z['lines'])))
        for k,y,e,ink,known in out:
            if ink and not known: print("   OUT   k=%3d  y=%6.1f  ink %.0f"%(k,y,e))

def columns_(pg, ks):
    """For each line k, the first and the last inked column."""
    z=np.load(f"{T}/cells/p-{pg:03d}.npz", allow_pickle=True)
    lg=np.array(z['lignes']); vstep=float(z['pasv']); hstep=float(z['pash'])
    xg=float(z['xg']); col0=int(z['col0'])
    a=P.load_(f"{ROOT}/scan/p-{pg:03d}.jpg")
    b=P.mask_edges(P.normalise(a)); _,r=P.deskew(b)
    H,W=r.shape; y0=float(lg[0,1]); k0=int(lg[0,0])
    out={}
    for k in ks:
        y=y0+(k-k0)*vstep
        i0=max(int(round(y-0.45*vstep)),0); i1=min(int(round(y+0.45*vstep)),H)
        pv=r[i0:i1].sum(axis=0)
        xs=np.where(pv>max(pv.max()*0.10,0.5))[0]
        if not len(xs): out[k]=None; continue
        c0=int(round((xs.min()-xg)/hstep))-col0
        c1=int(round((xs.max()-xg)/hstep))-col0
        out[k]=(c0,c1)
    return out
