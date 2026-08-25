"""The cover: extraction, cleaning, separation and vectorisation.

Three choices decide the fidelity:

1. **Oversampling x4 before the thresholding.** The cover's lettering is 5 px
   tall; thresholding at the native resolution sticks the letters together and
   breaks the fine strokes. The interpolation keeps the ramp of grey and
   potrace draws true contours from it.
2. **Removing the spots, but only the ISOLATED ones.** A small spot stuck to a
   stroke is the dot of an i, an accent or a piece of punctuation: it is kept.
   Only the grain of the paper, isolated, is removed.
3. **Two tones for the portraits.** The faces are drawn in two values: a solid
   black and a middling stipple. A tracing at one level must choose between the
   two and loses the modelling. We therefore trace two layers -- a grey and a
   black -- and superimpose them.
"""
import numpy as np, os, subprocess, re
from PIL import Image
from scipy.ndimage import uniform_filter, label, binary_dilation, binary_closing, find_objects, maximum_filter
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT=_ROOT; TRV=f"{ROOT}/work/couv"; ORN=f"{ROOT}/ornements"
SUR=4                      # oversampling factor
SEUIL_GRIS=0.28            # grey layer : everything that carries ink
SEUIL_NOIR=0.62            # black layer: the solids
SEUIL_TRAIT=0.16           # floor of the local threshold for the lettering

def encre_monochrome(path_):
    """The cover is printed in a single ink: we project the RGB onto its
    principal axis, which separates ink from paper better than any single
    channel."""
    a=np.asarray(Image.open(path_).convert("RGB")).astype(np.float32)
    X=a.reshape(-1,3); mu=X.mean(0); Xc=X-mu
    w,v=np.linalg.eigh(np.cov(Xc.T)); axe=v[:,np.argmax(w)]
    p=Xc@axe; p=(p-p.min())/(p.max()-p.min())
    if p[X.sum(1).argmin()]>0.5: p=1-p
    return (p.reshape(a.shape[:2])*255).astype(np.uint8)

def normalise(g, w=81, q=99.5):
    ground=uniform_filter(g.astype(np.float32),size=w)
    d=np.clip(ground-g,0,None)
    return np.clip(d/np.percentile(d,q),0,1)

def surechantillonner(a, k=SUR):
    im=Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
    return np.asarray(im.resize((a.shape[1]*k,a.shape[0]*k),Image.LANCZOS)).astype(np.float32)/255.

def _disque(r):
    y,x=np.mgrid[-r:r+1,-r:r+1]; return (x*x+y*y)<=r*r

def enlever_grain(B, k=SUR, aire_gros=25, aire_min=2, rayon=13):
    """Removes the isolated spots; keeps those that touch the neighbourhood of a
    stroke (dots of i's, accents, punctuation)."""
    scale=float(k*k)   # the areas are expressed in pixels of the original image
    lab,nb=label(B)
    if nb==0: return B
    t=np.bincount(lab.ravel())
    big=np.where(t>=aire_gros*scale)[0]; big=big[big>0]
    res=np.isin(lab,big)
    voisin=binary_dilation(res,_disque(max(int(rayon*k/4),1)))
    moyennes=np.where((t>=aire_min*scale)&(t<aire_gros*scale))[0]; moyennes=moyennes[moyennes>0]
    if len(moyennes):
        m=np.isin(lab,moyennes)
        kept=np.unique(lab[m&voisin]); kept=kept[kept>0]
        res|=np.isin(lab,kept)
    return res

SEUIL_FAIBLE=0.26          # doubtful stroke: kept if it touches a sure stroke
PLANCHER_FAIBLE=0.09
SEUIL_PALE=0.55            # a component that never blackens is not text


def retirer_pale(B, u, threshold=SEUIL_PALE):
    """Removes the components that contain no truly black pixel.

    The hysteresis threshold is *relative* to a local maximum: in a white
    stretch, the local maximum is a speck of the paper, and the speck gets
    through. That is how the grain of the paper came back in whole clouds as
    soon as one stopped planing it down by size.

    The parting is physical and clear all the same: the characters are inked,
    the grain is not. Measured on the eight letters that had been lost -- the
    « FI » of FILOZOFIO, the « L » of DIL, the « S » of PARIS, the full stop of
    « A. LALANDE », the « I » of KONCIZA, the full stop of « 10.000 », the
    « L » of LINGUIST., the parenthesis of (FRANCIA) -- every one of them peaks
    between 0.90 and 1.00. Three quarters of the components, by contrast, top
    out below 0.40. Cutting at 0.55 leaves the letters a considerable margin.
    """
    lab, nb = label(B, np.ones((3, 3), int))
    if not nb:
        return B
    fort = np.zeros(nb + 1, bool)
    fort[lab[u > threshold]] = True
    fort[0] = False
    return fort[lab]

def binariser_trait(a, k=SUR, fort=0.50, faible=SEUIL_FAIBLE, fen=5, grain=False):
    """Lettering and rules: a local hysteresis threshold.

    The simple rule -- keep what exceeds half the local maximum -- lost the
    fine strokes next to a bold letter: under the first portrait, « PROF. DE
    TEOLOGIO / UNIV. PARIS / (FRANCIA) » came down to « EO OG O / PAR S /
    RAN A », and « lia laboro linguistikala » to « l a laboro l nguistikala ».

    We therefore proceed in two stages, as for a contour: a high threshold
    gives the sure stroke, a low one the doubtful stroke, and of the doubtful
    we keep everything that touches the sure. A pale hairline attached to a
    clean letter survives; an isolated speck does not.

    `grain` is false by default, and it must stay so. This function used to
    end with an enlever_grain() that removes any component of fewer than 25
    pixels more than three pixels from a large component -- that is, the rule
    « small and far from a large one » which we know to be wrong: the captions
    have no large component within reach. Before any despeckling at all, it
    erased the full stop of « A. LALANDE », the « FI » of « FILOZOFIO », the
    « L » of « DIL », the « S » of « PARIS », the « L » of « LINGUIST. », the
    parentheses of « (FRANCIA) », the « I » of « KONCIZA » and the full stop of
    « 10.000 » -- sixty-one zones of ink in all, every one of them present and
    clear in the scan.

    The despeckling belongs to the two passes of build_cover(), which judge by
    isolation and not by size. One instance alone decides what a smut is, and
    it is the one with the right criterion.
    """
    u=surechantillonner(a,k)
    loc=maximum_filter(u,size=fen*k)
    F=u>np.maximum(fort*loc, SEUIL_TRAIT)
    W=u>np.maximum(faible*loc, PLANCHER_FAIBLE)
    lab,nb=label(W, np.ones((3,3),int))
    if nb:
        kept=np.unique(lab[F]); kept=kept[kept>0]
        W=np.isin(lab,kept)
    return enlever_grain(W,k) if grain else W

def binariser_deux_tons(a, k=SUR, bottom=SEUIL_GRIS, top=SEUIL_NOIR):
    u=surechantillonner(a,k)
    return enlever_grain(u>bottom,k), enlever_grain(u>top,k,aire_gros=18)

def _pbm(B, path_):
    h,w=B.shape
    with open(path_,"wb") as f:
        f.write(b"P4\n%d %d\n"%(w,h)); f.write(np.packbits(B,axis=1).tobytes())

def draw(B, out_path, turd=0, alpha=1.0, opttol=0.2, dpi=None):
    """potrace -> SVG and PDF. dpi: reference resolution of the bitmap supplied."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    pbm=out_path+".pbm"; _pbm(B,pbm)
    dpi = dpi if dpi else 150*SUR
    for fmt,ext in (("svg",".svg"),("pdf",".pdf")):
        subprocess.run(["potrace","-b",fmt,"-t",str(turd),"-a",str(alpha),
                        "-O",str(opttol),"-r",str(dpi),"-o",
                        os.path.splitext(out_path)[0]+ext, pbm], check=True)
    os.remove(pbm)

def tracer_deux_tons(a, out_path, gris="#8c8c8c"):
    """Traces a two-value element: grey layer beneath, black layer above.
    Returns the path of the SVG."""
    Bg,Bn=binariser_deux_tons(a)
    base=os.path.splitext(out_path)[0]
    draw(Bg, base+"-gris.svg"); draw(Bn, base+"-noir.svg")
    def extract(f):
        s=open(f).read()
        m=re.search(r'(<svg[^>]*>)(.*?)(</svg>)', s, re.S)
        entete=m.group(1); body=m.group(2)
        return entete, body
    e1,c1=extract(base+"-gris.svg"); e2,c2=extract(base+"-noir.svg")
    c1=c1.replace('fill="#000000"', f'fill="{gris}"')
    open(out_path,"w").write(e1 + c1 + c2 + "</svg>")
    for f in (base+"-gris.svg",base+"-noir.svg",base+"-gris.pdf",base+"-noir.pdf"):
        if os.path.exists(f): os.remove(f)
    return out_path

def rendre(svg, png, width_=None, scale_=1):
    """largeur: the width wanted in pixels (takes precedence over echelle)."""
    cmd=["rsvg-convert","-b","white","-o",png]
    cmd += (["-w",str(int(width_))] if width_ else ["-z",str(scale_)])
    subprocess.run(cmd+[svg],check=False)
    return os.path.exists(png)
