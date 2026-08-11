# -*- coding: utf-8 -*-
"""Extraction de ce qui n'est pas dactylographie : lettres de section, signature.

En tete de chaque lettre de l'alphabet, le livre porte cette lettre composee en
grand corps dans une elzevir — ce n'est pas de la frappe et cela ne se decode
pas. La page de contrefacon porte en outre la signature autographe de l'auteur.
On les decoupe dans le scan et on les repose dans le fac-simile a leur place,
mesuree en fraction de feuille.
"""
import numpy as np, json, os, sys
from scipy.ndimage import label as cclabel, find_objects
from PIL import Image
RAC="/root/dicionario"; T=f"{RAC}/travail"
SECTIONS = {8:'A',60:'B',88:'C',102:'D',133:'E',164:'F',192:'G',213:'H',
            258:'K',333:'L',355:'M',396:'N',407:'O',422:'P',481:'Q',
            486:'R',514:'S',609:'U',614:'V',630:'W',631:'X'}

# Cinq sections ne s'ouvrent pas en tete de page : elles suivent la precedente
# au milieu d'une feuille. lettre() ne cherchait que dans le haut du scan — le
# livre restait donc sans grande capitale pour I, J, T, Y et Z. On donne pour
# celles-la la bande verticale ou chercher, en fraction de la hauteur de page.
# La liste est de paires, et non un dictionnaire : X et Y partagent la page 631.
SECTIONS_MILIEU = [(233,'I',(0.04,0.32)), (253,'J',(0.02,0.26)),
                   (572,'T',(0.28,0.62)), (631,'Y',(0.55,0.92)),
                   (633,'Z',(0.35,0.78))]
_ST=np.ones((3,3),int)

def _composantes(a, seuil=0.28):
    b = a < (a.mean()-seuil*a.std())
    m=int(0.03*min(a.shape)); b[:m]=False; b[-m:]=False; b[:,:m]=False; b[:,-m:]=False
    L,k=cclabel(b,structure=_ST)
    return L,k,find_objects(L)

def lettre(pg, hmax=0.28, bande=None):
    a=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    L,k,obj=_composantes(a)
    best=None
    for i,o in enumerate(obj):
        h=o[0].stop-o[0].start; w=o[1].stop-o[1].start
        if bande is not None:
            cy=(o[0].start+h/2)/H
            if not (bande[0] <= cy <= bande[1]): continue
        elif o[0].start > hmax*H: continue
        if not (25<=h<=110 and 6<=w<=120): continue
        cx=(o[1].start+w/2)/W
        if not (0.28<=cx<=0.75): continue
        aire=int((L[o]==i+1).sum())
        # Plancher de surface : il ecarte les caracteres tapes, qui pesent moins
        # de cent pixels. A 400 il ecartait aussi les capitales etroites — le
        # « I » de la page 233 pese 349 pixels, le « J » de la 253 en pese 365.
        if aire<300: continue
        if best is None or aire>best[0]: best=(aire,o,h,w)
    if best is None: return None
    _,o,h,w=best
    return dict(pagino=pg, x=int(o[1].start), y=int(o[0].start), h=int(h), w=int(w),
                fx=(o[1].start+w/2)/W, fy=(o[0].start+h/2)/H, W=int(W), H=int(H))

def signature(pg=2):
    a=np.asarray(Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')).astype(np.float32)
    H,W=a.shape
    L,k,obj=_composantes(a)
    best=None
    for i,o in enumerate(obj):
        h=o[0].stop-o[0].start; w=o[1].stop-o[1].start
        if h<60 or w<120: continue
        aire=int((L[o]==i+1).sum())
        if best is None or aire>best[0]: best=(aire,o,h,w)
    if best is None: return None
    _,o,h,w=best
    return dict(pagino=pg, x=int(o[1].start), y=int(o[0].start), h=int(h), w=int(w),
                fx=(o[1].start+w/2)/W, fy=(o[0].start+h/2)/H, W=int(W), H=int(H))

def executer():
    rep=f"{RAC}/ornements/letroj"; os.makedirs(rep, exist_ok=True)
    out=[]
    taches=[(pg,L,None) for pg,L in sorted(SECTIONS.items())] + SECTIONS_MILIEU
    for pg,L,bande in sorted(taches, key=lambda t:(t[0], t[1])):
        e=lettre(pg, bande=bande)
        if e is None: print("  lettre introuvable p%03d (%s)"%(pg,L)); continue
        e['litero']=L
        im=Image.open(f"{RAC}/scan/p-{pg:03d}.jpg").convert('L')
        m=6
        c=im.crop((e['x']-m, e['y']-m, e['x']+e['w']+m, e['y']+e['h']+m))
        c=c.resize((c.size[0]*4, c.size[1]*4), Image.LANCZOS)
        c=c.point(lambda v: 0 if v< c.getextrema()[0]+ (c.getextrema()[1]-c.getextrema()[0])*0.55 else 255)
        nom=f"litero-{L}.png"; c.save(f"{rep}/{nom}"); e['dosiero']=f"ornements/letroj/{nom}"
        out.append(e)
    s=signature()
    if s:
        # Le paraphe est une seule tache d'encre, mais le « M » de Marcel en
        # est detache : on elargit vers la gauche pour ne pas le tronquer.
        im=Image.open(f"{RAC}/scan/p-002.jpg").convert('L'); m=10
        # Le paraphe est une seule tache d'encre, mais le « M » de Marcel en
        # est detache, et le haut des hampes depasse la boite : on elargit a
        # gauche et vers le haut.
        # Deux boites, et non une seule. Celle du DECOUPAGE est large, pour ne
        # rogner ni les hampes ni le « M » de Marcel, detache du reste. Celle du
        # MASQUE reste serree sur l'encre : la boite large mordait sur les deux
        # lignes tapees au-dessus, et le texte y disparaissait.
        s['masque']=dict(x=s['x'], y=s['y'], w=s['w'], h=s['h'])
        mg=int(s['w']*0.30); mh=int(s['h']*0.45)
        c=im.crop((max(s['x']-mg,0), max(s['y']-mh,0), s['x']+s['w']+m, s['y']+s['h']+m))
        s['x']-=mg; s['w']+=mg; s['y']-=mh; s['h']+=mh
        c=c.resize((c.size[0]*4,c.size[1]*4), Image.LANCZOS)
        c.save(f"{rep}/signaturo.png"); s['dosiero']="ornements/letroj/signaturo.png"; s['litero']='signaturo'
        out.append(s)
    json.dump(out, open(f"{T}/ornements.json","w"), ensure_ascii=False, indent=1)
    print("ornements extraits :", len(out))
    for e in out: print(f"   {e['litero']:>10} p{e['pagino']:03d}  {e['w']}x{e['h']} px  centre ({e['fx']:.3f}, {e['fy']:.3f})")

if __name__=="__main__": executer()
