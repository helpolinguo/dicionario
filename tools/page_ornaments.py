# -*- coding: utf-8 -*-
"""Extracting what is not typewritten: section letters, signature.

At the head of each letter of the alphabet, the book carries that letter set
in a large size in an Elzevir -- it is not typing and it does not decode. The
copyright page carries the author's autograph signature besides. We cut them
out of the scan and lay them back in the facsimile in their place, measured as
a fraction of the sheet.
"""
import numpy as np, json, os, sys
from scipy.ndimage import label as cclabel, find_objects
from PIL import Image
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=_ROOT; T=f"{ROOT}/work"
SECTIONS = {8:'A',60:'B',88:'C',102:'D',133:'E',164:'F',192:'G',213:'H',
            258:'K',333:'L',355:'M',396:'N',407:'O',422:'P',481:'Q',
            486:'R',514:'S',609:'U',614:'V',630:'W',631:'X'}

# Five sections do not open at the head of a page: they follow the previous
# one in the middle of a sheet. lettre() looked only in the top of the scan --
# the book therefore stayed without a large capital for I, J, T, Y and Z. For
# those we give the vertical band to search in, as a fraction of the page
# height. The list is of pairs, and not a dictionary: X and Y share page 631.
SECTIONS_MIDDLE = [(233,'I',(0.04,0.32)), (253,'J',(0.02,0.26)),
                   (572,'T',(0.28,0.62)), (631,'Y',(0.55,0.92)),
                   (633,'Z',(0.35,0.78))]
_ST=np.ones((3,3),int)

def _components(a, threshold=0.28):
    b = a < (a.mean()-threshold*a.std())
    m=int(0.03*min(a.shape)); b[:m]=False; b[-m:]=False; b[:,:m]=False; b[:,-m:]=False
    L,k=cclabel(b,structure=_ST)
    return L,k,find_objects(L)

def letter(pg, hmax=0.28, band=None):
    a=np.asarray(Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    L,k,obj=_components(a)
    best=None
    for i,o in enumerate(obj):
        h=o[0].stop-o[0].start; w=o[1].stop-o[1].start
        if band is not None:
            cy=(o[0].start+h/2)/H
            if not (band[0] <= cy <= band[1]): continue
        elif o[0].start > hmax*H: continue
        if not (25<=h<=110 and 6<=w<=120): continue
        cx=(o[1].start+w/2)/W
        if not (0.28<=cx<=0.75): continue
        area=int((L[o]==i+1).sum())
        # An area floor: it sets aside the typed characters, which weigh less
        # than a hundred pixels. At 400 it also set aside the narrow capitals --
        # the « I » of page 233 weighs 349 pixels, the « J » of page 253 weighs 365.
        if area<300: continue
        if best is None or area>best[0]: best=(area,o,h,w)
    if best is None: return None
    _,o,h,w=best
    return dict(pagino=pg, x=int(o[1].start), y=int(o[0].start), h=int(h), w=int(w),
                fx=(o[1].start+w/2)/W, fy=(o[0].start+h/2)/H, W=int(W), H=int(H))

def signature(pg=2):
    a=np.asarray(Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    L,k,obj=_components(a)
    best=None
    for i,o in enumerate(obj):
        h=o[0].stop-o[0].start; w=o[1].stop-o[1].start
        if h<60 or w<120: continue
        area=int((L[o]==i+1).sum())
        if best is None or area>best[0]: best=(area,o,h,w)
    if best is None: return None
    _,o,h,w=best
    return dict(pagino=pg, x=int(o[1].start), y=int(o[0].start), h=int(h), w=int(w),
                fx=(o[1].start+w/2)/W, fy=(o[0].start+h/2)/H, W=int(W), H=int(H))

def run_step():
    rep=f"{ROOT}/ornaments/letroj"; os.makedirs(rep, exist_ok=True)
    out=[]
    blobs=[(pg,L,None) for pg,L in sorted(SECTIONS.items())] + SECTIONS_MIDDLE
    for pg,L,band in sorted(blobs, key=lambda t:(t[0], t[1])):
        e=letter(pg, band=band)
        if e is None: print("  letter not found p%03d (%s)"%(pg,L)); continue
        e['litero']=L
        im=Image.open(f"{ROOT}/scan/p-{pg:03d}.jpg").convert('L')
        m=6
        c=im.crop((e['x']-m, e['y']-m, e['x']+e['w']+m, e['y']+e['h']+m))
        c=c.resize((c.size[0]*4, c.size[1]*4), Image.LANCZOS)
        c=c.point(lambda v: 0 if v< c.getextrema()[0]+ (c.getextrema()[1]-c.getextrema()[0])*0.55 else 255)
        name_=f"litero-{L}.png"; c.save(f"{rep}/{name_}"); e['dosiero']=f"ornaments/letroj/{name_}"
        out.append(e)
    s=signature()
    if s:
        # The flourish is a single spot of ink, but the « M » of Marcel is
        # detached from it: we widen leftwards so as not to truncate it.
        im=Image.open(f"{ROOT}/scan/p-002.jpg").convert('L'); m=10
        # The flourish is a single spot of ink, but the « M » of Marcel is
        # detached from it, and the top of the ascenders overruns the box: we
        # widen to the left and upwards.
        # Two boxes, and not one. The CUTTING box is wide, so as to crop neither
        # the ascenders nor the « M » of Marcel, detached from the rest. The MASK
        # box stays tight on the ink: the wide box bit into the two lines typed
        # above, and the text disappeared there.
        s['masque']=dict(x=s['x'], y=s['y'], w=s['w'], h=s['h'])
        mg=int(s['w']*0.30); mh=int(s['h']*0.45)
        c=im.crop((max(s['x']-mg,0), max(s['y']-mh,0), s['x']+s['w']+m, s['y']+s['h']+m))
        s['x']-=mg; s['w']+=mg; s['y']-=mh; s['h']+=mh
        c=c.resize((c.size[0]*4,c.size[1]*4), Image.LANCZOS)
        c.save(f"{rep}/signaturo.png"); s['dosiero']="ornaments/letroj/signaturo.png"; s['litero']='signaturo'
        out.append(s)
    json.dump(out, open(f"{T}/ornements.json","w"), ensure_ascii=False, indent=1)
    print("ornements extraits :", len(out))
    for e in out: print(f"   {e['litero']:>10} p{e['pagino']:03d}  {e['w']}x{e['h']} px  centre ({e['fx']:.3f}, {e['fy']:.3f})")

if __name__=="__main__": run_step()
