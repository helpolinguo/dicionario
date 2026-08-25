# -*- coding: utf-8 -*-
"""An inventory of what is not typewritten.

The book is not a grid of characters throughout. It also carries: the cover,
which is a lithograph; blank pages; the author's autograph signature on the
copyright page; and, at the head of each letter of the alphabet, that letter
set in a large size in an Elzevir. None of these decodes: they are located,
measured and reproduced as they stand.

The cue needs no scale: on a typewritten page, every spot of ink is of much
the same height. What clearly exceeds the page's median height does not
belong to the typing.
"""
import numpy as np, os, sys, json
from scipy.ndimage import label as cclabel, find_objects
from PIL import Image
sys.path.insert(0,'/root/dicionario/outils')
ROOT="/root/dicionario"; T=f"{ROOT}/travail"
_ST=np.ones((3,3),int)

def analyser_page(pg):
    a=np.asarray(Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    b = a < (a.mean()-0.28*a.std())
    # we ignore the band of shadow at the edges
    m=int(0.03*min(H,W)); b[:m]=False; b[-m:]=False; b[:,:m]=False; b[:,-m:]=False
    L,k=cclabel(b, structure=_ST)
    if k==0: return dict(pagino=pg, encre=0, blanka=True, elementi=[])
    obj=find_objects(L)
    top=np.array([o[0].stop-o[0].start for o in obj])
    wide=np.array([o[1].stop-o[1].start for o in obj])
    area=np.array([int((L[o]==i+1).sum()) for i,o in enumerate(obj)])
    big=area>=25
    if big.sum()<20:
        return dict(pagino=pg, encre=int(area.sum()), blanka=True, elementi=[])
    hm=float(np.median(top[big]))
    el=[]
    for i,o in enumerate(obj):
        if area[i]<200: continue
        if top[i] < 2.2*hm and wide[i] < 6*hm: continue
        el.append(dict(y=int(o[0].start), x=int(o[1].start),
                       h=int(top[i]), w=int(wide[i]), aire=int(area[i]),
                       hauteur_relative=round(top[i]/hm,2)))
    el.sort(key=lambda e:-e['aire'])
    return dict(pagino=pg, encre=int(area.sum()), blanka=False,
                hauteur_mediane=round(hm,1), elementi=el[:12])

def run_step(out_path=f"{T}/horsgrille.json"):
    out=[]
    for pg in range(639):
        if not os.path.exists(f"{ROOT}/scan/p-{pg:03d}.jpg"): continue
        try: out.append(analyser_page(pg))
        except Exception as e: out.append(dict(pagino=pg, erreur=str(e)))
        if pg%50==0: print("  ...p%03d"%pg, flush=True)
    json.dump(out, open(out_path,'w'), ensure_ascii=False)
    bl=[o['pagino'] for o in out if o.get('blanka')]
    ho=[(o['pagino'], len(o['elementi'])) for o in out if o.get('elementi')]
    print("blank pages:", len(bl), bl)
    print("pages carrying an off-grid element:", len(ho))
    print(ho[:60])

if __name__=="__main__": run_step()
