"""Comparaison visuelle : page composee contre page scannee redressee et remise
a l'echelle de la grille restauree (10 caracteres au pouce)."""
import numpy as np, subprocess, os, sys
sys.path.insert(0,'/root/dicionario/outils')
from PIL import Image
from scipy.ndimage import rotate as ndrotate
from page import charger, normaliser, desincliner, masquer_bords
RAC="/root/dicionario"
PASH_IN=0.1; PASV_IN=0.170128; ORIGX_MM=21.9; ORIGY_MM=14.3

def scan_cale(pg, dpi=150):
    """Scan redresse, remis a l'echelle de la grille et cale sur l'origine du
    document compose. La photographie varie d'echelle et de cadrage : ces deux
    variations ne sont pas des proprietes du livre."""
    a=charger(f"{RAC}/scan/p-{pg:03d}.jpg")
    ang,_=desincliner(masquer_bords(normaliser(a)))
    r=np.clip(ndrotate(a, ang, reshape=False, order=1, mode='constant', cval=255),0,255)
    z=np.load(f"{RAC}/travail/cellules/p-{pg:03d}.npz", allow_pickle=True)
    kx=(dpi*PASH_IN)/float(z['pash']); ky=(dpi*PASV_IN)/float(z['pasv'])
    x0=(float(z['xg'])+int(z['col0'])*float(z['pash']))*kx
    y0=float(z['lignes'][0,1])*ky
    im=Image.fromarray(r.astype(np.uint8)).resize(
        (max(int(r.shape[1]*kx),1), max(int(r.shape[0]*ky),1)), Image.LANCZOS)
    W=int(210/25.4*dpi); H=int(297/25.4*dpi)
    dx=int(round(ORIGX_MM/25.4*dpi - x0)); dy=int(round(ORIGY_MM/25.4*dpi - y0))
    out=Image.new("L",(W,H),255)
    out.paste(im,(dx,dy))
    return out

def rendre_compose(pdf, page, dpi=150, pre="/tmp/cmp"):
    subprocess.run(["pdftoppm","-r",str(dpi),"-gray","-png","-f",str(page),"-l",str(page),
                    pdf,pre],check=True)
    for c in (f"{pre}-{page}.png", f"{pre}-{page:02d}.png", f"{pre}-{page:03d}.png"):
        if os.path.exists(c): return c
    raise FileNotFoundError

def superposer(pdf, page, pg, sortie, dpi=150, crop=None, zoom=1):
    """Scan en vert, composition en rouge ; noir = les deux coincident."""
    a=np.asarray(Image.open(rendre_compose(pdf,page,dpi)).convert("L"))
    b=np.asarray(scan_cale(pg,dpi))
    H=min(a.shape[0],b.shape[0]); W=min(a.shape[1],b.shape[1])
    a=a[:H,:W]; b=b[:H,:W]
    im=Image.fromarray(np.stack([b,a,np.minimum(a,b)],-1).astype(np.uint8))
    if crop: im=im.crop(crop)
    if zoom!=1: im=im.resize((im.size[0]*zoom,im.size[1]*zoom), Image.LANCZOS)
    im.save(sortie)
    ai=a<160; bi=b<160
    return dict(jaccard=float((ai&bi).sum()/max((ai|bi).sum(),1)))

def cote_a_cote(pdf, page, pg, sortie, dpi=150):
    a=Image.open(rendre_compose(pdf,page,dpi)).convert("L"); b=scan_cale(pg,dpi)
    out=Image.new("L",(a.size[0]+b.size[0]+16,max(a.size[1],b.size[1])),255)
    out.paste(b,(0,0)); out.paste(a,(b.size[0]+16,0)); out.save(sortie)
    return out.size
