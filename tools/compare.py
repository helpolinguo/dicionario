"""Visual comparison: the composed page against the scanned page deskewed
and brought back to the scale of the restored grid (10 characters to the
inch)."""
import numpy as np, subprocess, os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from PIL import Image
from scipy.ndimage import rotate as ndrotate
from page import load_, normalise, deskew, mask_edges
ROOT=_ROOT
HSTEP_IN=0.1; VSTEP_IN=0.170128; ORIGX_MM=21.9; ORIGY_MM=14.3

def scan_wedged(pg, dpi=150):
    """The scan deskewed, brought back to the grid's scale and set on the origin
    of the composed document. The photograph varies in scale and in framing:
    neither variation is a property of the book."""
    a=load_(f"{ROOT}/scan/p-{pg:03d}.jpg")
    angle_,_=deskew(mask_edges(normalise(a)))
    r=np.clip(ndrotate(a, angle_, reshape=False, order=1, mode='constant', cval=255),0,255)
    z=np.load(f"{ROOT}/work/cells/p-{pg:03d}.npz", allow_pickle=True)
    kx=(dpi*HSTEP_IN)/float(z['pash']); ky=(dpi*VSTEP_IN)/float(z['pasv'])
    x0=(float(z['xg'])+int(z['col0'])*float(z['pash']))*kx
    y0=float(z['lignes'][0,1])*ky
    im=Image.fromarray(r.astype(np.uint8)).resize(
        (max(int(r.shape[1]*kx),1), max(int(r.shape[0]*ky),1)), Image.LANCZOS)
    W=int(210/25.4*dpi); H=int(297/25.4*dpi)
    dx=int(round(ORIGX_MM/25.4*dpi - x0)); dy=int(round(ORIGY_MM/25.4*dpi - y0))
    out=Image.new("L",(W,H),255)
    out.paste(im,(dx,dy))
    return out

def render_compound(pdf, page, dpi=150, pre="/tmp/cmp"):
    subprocess.run(["pdftoppm","-r",str(dpi),"-gray","-png","-f",str(page),"-l",str(page),
                    pdf,pre],check=True)
    for c in (f"{pre}-{page}.png", f"{pre}-{page:02d}.png", f"{pre}-{page:03d}.png"):
        if os.path.exists(c): return c
    raise FileNotFoundError

def overlay(pdf, page, pg, out_path, dpi=150, crop=None, zoom=1):
    """Scan in green, composition in red; black = the two coincide."""
    a=np.asarray(Image.open(render_compound(pdf,page,dpi)).convert("L"))
    b=np.asarray(scan_wedged(pg,dpi))
    H=min(a.shape[0],b.shape[0]); W=min(a.shape[1],b.shape[1])
    a=a[:H,:W]; b=b[:H,:W]
    im=Image.fromarray(np.stack([b,a,np.minimum(a,b)],-1).astype(np.uint8))
    if crop: im=im.crop(crop)
    if zoom!=1: im=im.resize((im.size[0]*zoom,im.size[1]*zoom), Image.LANCZOS)
    im.save(out_path)
    ai=a<160; bi=b<160
    return dict(jaccard=float((ai&bi).sum()/max((ai|bi).sum(),1)))

def side_by_side(pdf, page, pg, out_path, dpi=150):
    a=Image.open(render_compound(pdf,page,dpi)).convert("L"); b=scan_wedged(pg,dpi)
    out=Image.new("L",(a.size[0]+b.size[0]+16,max(a.size[1],b.size[1])),255)
    out.paste(b,(0,0)); out.paste(a,(b.size[0]+16,0)); out.save(out_path)
    return out.size
