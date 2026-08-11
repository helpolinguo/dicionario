"""Couverture : extraction, nettoyage, separation et vectorisation.

Trois choix decident de la fidelite :

1. **Sur-echantillonnage x4 avant le seuillage.** Les lettrages de la couverture
   ont 5 px de haut ; seuiller a la definition native colle les lettres entre
   elles et casse les traits fins. L'interpolation conserve la rampe de gris et
   potrace en tire des contours justes.
2. **Retrait des taches, mais seulement des taches ISOLEES.** Une petite tache
   collee a un trait est un point d'i, un accent ou une ponctuation : elle est
   conservee. Seul le grain du papier, isole, est retire.
3. **Deux tons pour les portraits.** Les visages sont dessines en deux valeurs :
   un aplat noir et un pointille moyen. Un trace a un seul niveau doit choisir
   entre les deux et perd le modele. On trace donc deux calques — un gris et un
   noir — et on les superpose.
"""
import numpy as np, os, subprocess, re
from PIL import Image
from scipy.ndimage import uniform_filter, label, binary_dilation, binary_closing, find_objects, maximum_filter
RAC="/root/dicionario"; TRV=f"{RAC}/travail/couv"; ORN=f"{RAC}/ornements"
SUR=4                      # facteur de sur-echantillonnage
SEUIL_GRIS=0.28            # calque gris  : tout ce qui porte de l'encre
SEUIL_NOIR=0.62            # calque noir  : les aplats
SEUIL_TRAIT=0.16           # plancher du seuil local pour les lettrages

def encre_monochrome(chemin):
    """La couverture est imprimee en une seule encre : on projette le RVB sur
    son axe principal, ce qui separe l'encre du papier mieux qu'un canal isole."""
    a=np.asarray(Image.open(chemin).convert("RGB")).astype(np.float32)
    X=a.reshape(-1,3); mu=X.mean(0); Xc=X-mu
    w,v=np.linalg.eigh(np.cov(Xc.T)); axe=v[:,np.argmax(w)]
    p=Xc@axe; p=(p-p.min())/(p.max()-p.min())
    if p[X.sum(1).argmin()]>0.5: p=1-p
    return (p.reshape(a.shape[:2])*255).astype(np.uint8)

def normaliser(g, w=81, q=99.5):
    fond=uniform_filter(g.astype(np.float32),size=w)
    d=np.clip(fond-g,0,None)
    return np.clip(d/np.percentile(d,q),0,1)

def surechantillonner(a, k=SUR):
    im=Image.fromarray((np.clip(a,0,1)*255).astype(np.uint8))
    return np.asarray(im.resize((a.shape[1]*k,a.shape[0]*k),Image.LANCZOS)).astype(np.float32)/255.

def _disque(r):
    y,x=np.mgrid[-r:r+1,-r:r+1]; return (x*x+y*y)<=r*r

def enlever_grain(B, k=SUR, aire_gros=25, aire_min=2, rayon=13):
    """Retire les taches isolees ; garde celles qui touchent le voisinage d'un
    trait (points d'i, accents, ponctuation)."""
    ech=float(k*k)   # les aires sont exprimees en pixels de l'image d'origine
    lab,nb=label(B)
    if nb==0: return B
    t=np.bincount(lab.ravel())
    gros=np.where(t>=aire_gros*ech)[0]; gros=gros[gros>0]
    res=np.isin(lab,gros)
    voisin=binary_dilation(res,_disque(max(int(rayon*k/4),1)))
    moyennes=np.where((t>=aire_min*ech)&(t<aire_gros*ech))[0]; moyennes=moyennes[moyennes>0]
    if len(moyennes):
        m=np.isin(lab,moyennes)
        garde=np.unique(lab[m&voisin]); garde=garde[garde>0]
        res|=np.isin(lab,garde)
    return res

SEUIL_FAIBLE=0.26          # trait douteux : garde s'il touche du trait sur
PLANCHER_FAIBLE=0.09
SEUIL_PALE=0.55            # une composante qui ne noircit jamais n'est pas du texte


def retirer_pale(B, u, seuil=SEUIL_PALE):
    """Retire les composantes qui ne contiennent aucun pixel vraiment noir.

    Le seuil a hysteresis est *relatif* a un maximum local : dans une plage
    blanche, le maximum local est une moucheture du papier, et la moucheture
    passe. C'est ainsi que le grain du papier remontait par nuages entiers des
    que l'on cessait de le raboter a la taille.

    Le depart est pourtant physique et net : les caracteres sont encres, le
    grain ne l'est pas. Mesure sur les huit lettres qu'on avait perdues — le
    « FI » de FILOZOFIO, le « L » de DIL, le « S » de PARIS, le point de
    « A. LALANDE », le « I » de KONCIZA, le point de « 10.000 », le « L » de
    LINGUIST., la parenthese de (FRANCIA) — toutes culminent entre 0,90 et
    1,00. Les trois quarts des composantes, elles, plafonnent sous 0,40.
    Couper a 0,55 laisse aux lettres une marge considerable.
    """
    lab, nb = label(B, np.ones((3, 3), int))
    if not nb:
        return B
    fort = np.zeros(nb + 1, bool)
    fort[lab[u > seuil]] = True
    fort[0] = False
    return fort[lab]

def binariser_trait(a, k=SUR, fort=0.50, faible=SEUIL_FAIBLE, fen=5, grain=False):
    """Lettrages et filets : seuil local a hysteresis.

    La regle simple — garder ce qui depasse la moitie du maximum local —
    perdait les traits fins voisins d'une lettre grasse : sous le premier
    portrait, « PROF. DE TEOLOGIO / UNIV. PARIS / (FRANCIA) » se reduisait a
    « EO OG O / PAR S / RAN A », et « lia laboro linguistikala » a
    « l a laboro l nguistikala ».

    On procede donc en deux temps, comme pour un contour : un seuil haut donne
    le trait sur, un seuil bas le trait douteux, et l'on garde du douteux tout
    ce qui touche du sur. Un delie pale rattache a une lettre nette survit ;
    une moucheture isolee, non.

    `grain` est faux par defaut, et il faut qu'il le reste. Cette fonction se
    terminait par un enlever_grain() qui retire toute composante de moins de
    25 pixels a plus de trois pixels d'une gross composante — c'est-a-dire la
    regle « petit et loin d'un gros » dont on sait qu'elle est fausse : les
    legendes n'ont pas de grosse composante a portee. Elle effacait, avant
    meme tout depoussierage, le point de « A. LALANDE », le « FI » de
    « FILOZOFIO », le « L » de « DIL », le « S » de « PARIS », le « L » de
    « LINGUIST. », les parentheses de « (FRANCIA) », le « I » de
    « KONCIZA » et le point de « 10.000 » — soixante et une zones d'encre en
    tout, toutes presentes et franches dans le scan.

    Le depoussierage appartient aux deux passes de faire_couverture(), qui
    jugent par l'isolement et non par la taille. Une seule instance decide de
    ce qu'est une salissure, et c'est celle qui a le bon critere.
    """
    u=surechantillonner(a,k)
    loc=maximum_filter(u,size=fen*k)
    F=u>np.maximum(fort*loc, SEUIL_TRAIT)
    W=u>np.maximum(faible*loc, PLANCHER_FAIBLE)
    lab,nb=label(W, np.ones((3,3),int))
    if nb:
        garde=np.unique(lab[F]); garde=garde[garde>0]
        W=np.isin(lab,garde)
    return enlever_grain(W,k) if grain else W

def binariser_deux_tons(a, k=SUR, bas=SEUIL_GRIS, haut=SEUIL_NOIR):
    u=surechantillonner(a,k)
    return enlever_grain(u>bas,k), enlever_grain(u>haut,k,aire_gros=18)

def _pbm(B, chemin):
    h,w=B.shape
    with open(chemin,"wb") as f:
        f.write(b"P4\n%d %d\n"%(w,h)); f.write(np.packbits(B,axis=1).tobytes())

def tracer(B, sortie, turd=0, alpha=1.0, opttol=0.2, dpi=None):
    """potrace -> SVG et PDF. dpi : definition de reference du bitmap fourni."""
    os.makedirs(os.path.dirname(sortie) or ".", exist_ok=True)
    pbm=sortie+".pbm"; _pbm(B,pbm)
    dpi = dpi if dpi else 150*SUR
    for fmt,ext in (("svg",".svg"),("pdf",".pdf")):
        subprocess.run(["potrace","-b",fmt,"-t",str(turd),"-a",str(alpha),
                        "-O",str(opttol),"-r",str(dpi),"-o",
                        os.path.splitext(sortie)[0]+ext, pbm], check=True)
    os.remove(pbm)

def tracer_deux_tons(a, sortie, gris="#8c8c8c"):
    """Trace un element a deux valeurs : calque gris dessous, calque noir dessus.
    Retourne le chemin du SVG."""
    Bg,Bn=binariser_deux_tons(a)
    base=os.path.splitext(sortie)[0]
    tracer(Bg, base+"-gris.svg"); tracer(Bn, base+"-noir.svg")
    def extraire(f):
        s=open(f).read()
        m=re.search(r'(<svg[^>]*>)(.*?)(</svg>)', s, re.S)
        entete=m.group(1); corps=m.group(2)
        return entete, corps
    e1,c1=extraire(base+"-gris.svg"); e2,c2=extraire(base+"-noir.svg")
    c1=c1.replace('fill="#000000"', f'fill="{gris}"')
    open(sortie,"w").write(e1 + c1 + c2 + "</svg>")
    for f in (base+"-gris.svg",base+"-noir.svg",base+"-gris.pdf",base+"-noir.pdf"):
        if os.path.exists(f): os.remove(f)
    return sortie

def rendre(svg, png, largeur=None, echelle=1):
    """largeur : largeur voulue en pixels (prioritaire sur echelle)."""
    cmd=["rsvg-convert","-b","white","-o",png]
    cmd += (["-w",str(int(largeur))] if largeur else ["-z",str(echelle)])
    subprocess.run(cmd+[svg],check=False)
    return os.path.exists(png)
