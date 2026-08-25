# -*- coding: utf-8 -*-
"""Direct proofreading, page by page: the image of the scan against the
decoded text.

Every preceding method was indirect -- grouping the shapes, labelling the
groups, correcting by the lexicon. They carried the book from 93 % to a
little over 99 %, but 99 % still leaves some ten faults a page. To go beyond
that one must read.

The grid makes the thing exact: one cell, one character. The proofreader
therefore receives each decoded line and must return a line of the **same
length**. A missing letter replaces a space, a letter too many becomes a
space again, and the matching is done column by column, without ambiguity.
"""
import numpy as np, os, sys, json
from PIL import Image, ImageDraw
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
ROOT=_ROOT; T=f"{ROOT}/work"
ZOOM=1.7; BANDES=3; CHEV=2      # overlap, in lines

def texte_page(pg, pages=None):
    if pages is None:
        from edition import load_text
        pages,_,_=load_text()
    return pages.get(pg, [])

def strips(pg, rep, lines):
    """Cuts the page into horizontal strips, each legible at a glance."""
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    scale=float(z['shape'][0])/Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").size[1]
    vstep=float(z['pasv']); lg={int(k):float(y) for k,y in z['lignes']}
    im=Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert('L')
    W,H=im.size
    ks=sorted(lg)
    n=max(1,(len(ks)+BANDES-1)//BANDES)
    out=[]
    for b in range(0, len(ks), n):
        sous=ks[max(b-CHEV,0): b+n+CHEV]
        if not sous: continue
        y0=max(int((lg[sous[0]]-1.2*vstep)/scale), 0)
        y1=min(int((lg[sous[-1]]+1.2*vstep)/scale), H)
        c=im.crop((0,y0,W,y1))
        c=c.resize((int(W*ZOOM), int((y1-y0)*ZOOM)), Image.LANCZOS)
        name_=f"{rep}/p{pg:03d}b{b//n}.png"; c.save(name_)
        out.append(dict(fichier=os.path.basename(name_), lignes=[k for k in ks[b:b+n]]))
    return out

def preparer(pgs, rep=f"{T}/relecture"):
    os.makedirs(rep, exist_ok=True)
    from edition import load_text
    pages,_,_=load_text()
    records=[]
    for pg in pgs:
        lines=dict(texte_page(pg, pages))
        bs=strips(pg, rep, lines)
        with open(f"{rep}/p{pg:03d}.txt","w",encoding='utf-8') as f:
            for b in bs:
                f.write(f"== {b['fichier']}\n")
                for k in b['lignes']:
                    f.write(f"{k:03d}|{lines.get(k,'')}\n")
        records.append(dict(pagino=pg, bandes=bs))
    json.dump(records, open(f"{rep}/fiches.json","w"))
    return records

if __name__=="__main__":
    pgs=[int(x) for x in sys.argv[1:]]
    f=preparer(pgs)
    print("pages prepared:", len(f), " bandes :", sum(len(x['bandes']) for x in f))
