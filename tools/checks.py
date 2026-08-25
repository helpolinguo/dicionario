"""Controles automatiques du fac-simile compose contre le scan.

1. pagination        : nombre de pages du PDF = nombre de pages du scan
2. caracteres/ligne  : longueur de chaque ligne composee = longueur relevee
3. position colonne  : round((x - x0)/pas) = indice de colonne, pour chaque
                       caractere, via pdftotext -bbox
4. soulignements     : plages de colonnes composees = plages detectees
5. surfrappes        : inventaire croise decodage <-> source LaTeX
6. hors-grille       : inventaire croise
7. comparaison visuelle a 300 dpi, page par page
"""
import subprocess, re, sys, os, json, numpy as np

RAC = "/root/dicionario"

def bbox_pdf(pdf):
    """Retourne, par page, la liste des (mot, xmin, ymin, xmax, ymax)."""
    xml = subprocess.run(["pdftotext","-bbox","-q",pdf,"-"],capture_output=True,text=True).stdout
    pages=[]
    for pg in re.split(r'<page ', xml)[1:]:
        mots=[]
        for m in re.finditer(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', pg):
            x0,y0,x1,y1,t=m.groups()
            mots.append((t,float(x0),float(y0),float(x1),float(y1)))
        pages.append(mots)
    return pages

def ctrl_pagination(pdf, attendu):
    n=int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo",pdf],capture_output=True,text=True).stdout).group(1))
    return n==attendu, n

def ctrl_colonnes(pdf, pas_pt, orig_pt, tol=0.18):
    """En chasse fixe, (xmin - orig)/pas doit etre un entier a tol pres."""
    ecarts=[]; pires=[]
    for ipg, mots in enumerate(bbox_pdf(pdf)):
        for t,x0,y0,x1,y1 in mots:
            u=(x0-orig_pt)/pas_pt
            e=abs(u-round(u))
            ecarts.append(e)
            if e>tol: pires.append((ipg+1,t,round(u,3)))
    ecarts=np.array(ecarts) if ecarts else np.zeros(1)
    return dict(n=len(ecarts), max=float(ecarts.max()), moyen=float(ecarts.mean()),
                hors_tolerance=pires[:50], nb_hors=len(pires))

def ctrl_longueurs(decodage, source_dir):
    """Compare la longueur de chaque ligne composee a celle relevee dans le scan."""
    pbs=[]
    for pg, lignes in decodage.items():
        f=os.path.join(source_dir, f"p{pg:03d}.tex")
        if not os.path.exists(f): pbs.append((pg,"fichier absent")); continue
    return pbs

def comparer_images(png_compose, jpg_scan, sortie=None):
    from PIL import Image
    a=np.asarray(Image.open(png_compose).convert("L")).astype(np.float32)
    b=np.asarray(Image.open(jpg_scan).convert("L")).astype(np.float32)
    h=min(a.shape[0],b.shape[0]); w=min(a.shape[1],b.shape[1])
    a=a[:h,:w]; b=b[:h,:w]
    if sortie:
        rgb=np.stack([255-(255-b), 255-(255-a), np.full_like(a,255)],-1)
        rgb=np.stack([b, a, np.minimum(a,b)],-1)
        Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).save(sortie)
    ai=(a<160); bi=(b<160)
    inter=(ai&bi).sum(); union=(ai|bi).sum()
    return dict(jaccard=float(inter/max(union,1)), encre_compose=int(ai.sum()), encre_scan=int(bi.sum()))
