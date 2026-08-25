"""Prepares a page's proofreading sheets: one line of the book per line of
image, columns numbered, plus the current decoding alongside."""
import sys, os, numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from line_images import image_lignes
from decode import load_, page_text
from generate import exceptions
T=_ROOT + "/work"

def preparer(pg, rep=None, per=12, zoom=4):
    rep = rep or f"{T}/relecture/p{pg:03d}"
    os.makedirs(rep, exist_ok=True)
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    c=z['cells']; lg=z['lignes']; occ=z['occ']
    for a in range(0, c.shape[0], per):
        image_lignes(c[a:a+per], lignes_ids=[int(x) for x in lg[a:a+per,0]], zoom=zoom
                     ).save(f"{rep}/planche{a//per:02d}.png")
    lab,M=load_(); tab=np.load(f"{T}/cls_lab.npy", allow_pickle=True)
    exc=exceptions()
    lines=[]
    for k,s in page_text(pg,lab,M,tab):
        l=list(s)
        for (pp,kk,cc),v in exc.items():
            if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
        lines.append((k,"".join(l).rstrip()))
    with open(f"{rep}/decodage.txt","w",encoding='utf-8') as f:
        for k,s in lines: f.write(f"{k}\t{s}\n")
    with open(f"{rep}/occupation.txt","w",encoding='utf-8') as f:
        for i,k in enumerate(lg[:,0]):
            f.write(f"{int(k)}\t" + "".join("#" if o else "." for o in occ[i]) + "\n")
    return rep, (c.shape[0]+per-1)//per

if __name__=="__main__":
    for a in sys.argv[1:]:
        print(preparer(int(a)))
