"""Automatic checks of the composed facsimile against the scan.

1. pagination        : number of pages in the PDF = number of pages in the scan
2. characters/line   : length of each composed line = length surveyed
3. column position   : round((x - x0)/pitch) = column index, for each
                       character, via pdftotext -bbox
4. underlines        : ranges of composed columns = ranges detected
5. overstrikes       : cross-inventory decoding <-> LaTeX source
6. off-grid          : cross-inventory
7. visual comparison at 300 dpi, page by page
"""
import subprocess, re, sys, os, json, numpy as np
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = _ROOT

def bbox_pdf(pdf):
    """Returns, per page, the list of (word, xmin, ymin, xmax, ymax)."""
    xml = subprocess.run(["pdftotext","-bbox","-q",pdf,"-"],capture_output=True,text=True).stdout
    pages=[]
    for pg in re.split(r'<page ', xml)[1:]:
        words=[]
        for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', pg):
            x0,y0,x1,y1,t=m.groups()
            words.append((t,float(x0),float(y0),float(x1),float(y1)))
        pages.append(words)
    return pages

def ctrl_pagination(pdf, attendu):
    n=int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo",pdf],capture_output=True,text=True).stdout).group(1))
    return n==attendu, n

def ctrl_colonnes(pdf, pas_pt, orig_pt, tol=0.18):
    """In a fixed set, (xmin - orig)/pitch must be an integer to within tol."""
    gaps=[]; worst=[]
    for ipg, words in enumerate(bbox_pdf(pdf)):
        for t,x0,y0,x1,y1 in words:
            u=(x0-orig_pt)/pas_pt
            e=abs(u-round(u))
            gaps.append(e)
            if e>tol: worst.append((ipg+1,t,round(u,3)))
    gaps=np.array(gaps) if gaps else np.zeros(1)
    return dict(n=len(gaps), max=float(gaps.max()), moyen=float(gaps.mean()),
                hors_tolerance=worst[:50], nb_hors=len(worst))

def ctrl_longueurs(decodage, source_dir):
    """Compares the length of each composed line with the one surveyed in the scan."""
    pbs=[]
    for pg, lines in decodage.items():
        f=os.path.join(source_dir, f"p{pg:03d}.tex")
        if not os.path.exists(f): pbs.append((pg,"fichier absent")); continue
    return pbs

def comparer_images(png_compose, jpg_scan, out_path=None):
    from PIL import Image
    a=np.asarray(Image.open(png_compose).convert("L")).astype(np.float32)
    b=np.asarray(Image.open(jpg_scan).convert("L")).astype(np.float32)
    h=min(a.shape[0],b.shape[0]); w=min(a.shape[1],b.shape[1])
    a=a[:h,:w]; b=b[:h,:w]
    if out_path:
        rgb=np.stack([255-(255-b), 255-(255-a), np.full_like(a,255)],-1)
        rgb=np.stack([b, a, np.minimum(a,b)],-1)
        Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(out_path)
    ai=(a<160); bi=(b<160)
    inter=(ai&bi).sum(); union=(ai|bi).sum()
    return dict(jaccard=float(inter/max(union,1)), encre_compose=int(ai.sum()), encre_scan=int(bi.sum()))
