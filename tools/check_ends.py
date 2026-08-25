# -*- coding: utf-8 -*-
"""How many characters does the block cut off at the end of a line?
A measurement, not an opinion.

We re-cut each page with the block extended to the right -- recording
nothing -- and count the occupied cells that fall beyond the current block.
Those are exactly the lost characters.
"""
import sys, os, json
import numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
import cells
ROOT=_ROOT; T=f"{ROOT}/work"

def one_(pg):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    ncol=z['occ'].shape[1]; col0=int(z['col0'])
    cells.ETENDRE=False; cells.ETENDRE_D=True
    d=cells.extract(f"{ROOT}/scan/p-{pg:03d}.jpg")
    occ=d['occ']; c0=int(d['col0'])
    # columns of the extension: beyond (col0-c0) + ncol in the extended frame
    start_=(col0-c0)+ncol
    if start_ >= occ.shape[1]: return dict(pagino=pg, perdus=0, lignes=0, colonnes=0)
    sup=occ[:, start_:]
    lines=int((sup.sum(1)>0).sum())
    return dict(pagino=pg, perdus=int(sup.sum()), lignes=lines,
                colonnes=int(occ.shape[1]-start_))

if __name__=="__main__":
    a,b=int(sys.argv[1]), int(sys.argv[2]); out=[]
    for pg in range(a,b):
        if not os.path.exists(f"{T}/cellules/p-{pg:03d}.npz"): continue
        if pg in (0,1,3,7,87,111,577): continue
        try: out.append(one_(pg))
        except Exception as e: print("ECHEC",pg,e, flush=True)
    json.dump(out, open(f"{T}/fins_{a}.json","w"))
    p=sum(x['perdus'] for x in out); l=sum(x['lignes'] for x in out)
    print(f"{a}-{b} : {len(out)} pages, {l} lines touched, {p} characters cut off")
