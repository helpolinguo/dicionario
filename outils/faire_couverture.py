"""Reconstruit tous les elements de la couverture."""
import sys, numpy as np, os, re, shutil, subprocess
sys.path.insert(0,'/root/dicionario/outils')
from couverture import *
from PIL import Image
from scipy.ndimage import label, binary_closing, find_objects

NOMS=["beaufront","couturat","jespersen","lalande","lorenz","ostwald","pfaundler"]
BOITES=[(21,138,264,394),(188,288,218,359),(379,458,187,331),(546,638,175,323),
        (720,801,188,330),(877,974,218,358),(1034,1136,285,394)]

def corps(f):
    s=open(f).read(); m=re.search(r'(<svg[^>]*>)(.*?)(</svg>)',s,re.S); return m.group(1),m.group(2)

def fusionner(gris_svg, noir_svg, sortie, gris="#8c8c8c"):
    e,cg=corps(gris_svg); _,cn=corps(noir_svg)
    open(sortie,"w").write(e+cg.replace('fill="#000000"',f'fill="{gris}"')+cn+"</svg>")
    subprocess.run(["rsvg-convert","-f","pdf","-o",os.path.splitext(sortie)[0]+".pdf",sortie],check=False)
    for f in (gris_svg,noir_svg,os.path.splitext(gris_svg)[0]+".pdf",os.path.splitext(noir_svg)[0]+".pdf"):
        if os.path.exists(f): os.remove(f)

def executer():
    g=encre_monochrome(f"{RAC}/scan/p-000.jpg")
    n=normaliser(g)[4:1640,0:1205]
    os.makedirs(TRV,exist_ok=True); np.save(f"{TRV}/niveaux.npy",n)
    u=surechantillonner(n)

    # --- portraits : deux tons ---
    shutil.rmtree(f"{ORN}/portraits",ignore_errors=True); os.makedirs(f"{ORN}/portraits")
    for (x0,x1,y0,y1),nom in zip(BOITES,NOMS):
        m=6; a,b,c,d=max(x0-m,0),min(x1+m,n.shape[1]),max(y0-m,0),min(y1+m,n.shape[0])
        z=n[c:d,a:b]
        Bg,Bn=binariser_deux_tons(z)
        tracer(Bg,f"{ORN}/portraits/{nom}-g.svg"); tracer(Bn,f"{ORN}/portraits/{nom}-n.svg")
        fusionner(f"{ORN}/portraits/{nom}-g.svg",f"{ORN}/portraits/{nom}-n.svg",f"{ORN}/portraits/{nom}.svg")
        rendre(f"{ORN}/portraits/{nom}.svg",f"{ORN}/portraits/{nom}-x6.png",largeur=(b-a)*6)
        Image.fromarray((np.clip(1-z,0,1)*255).astype(np.uint8)).resize(((b-a)*6,(d-c)*6),Image.LANCZOS)\
             .save(f"{ORN}/portraits/{nom}-gris-x6.png")

    # --- couverture complete : lettrages au trait + portraits a deux tons ---
    noir=binariser_trait(n); gris=np.zeros_like(noir)
    # Le mot « invitas » est efface au scan : on lui rend son « i » et son « t »,
    # pris dans « profitar ». Voir outils/reparer_couverture.py.
    from reparer_couverture import appliquer as _reparer_invitas
    noir=_reparer_invitas(noir)
    # Le grain du papier n'est jamais vraiment noir : on le retire par le
    # niveau d'encre, avant de juger quoi que ce soit par la taille.
    _av=noir.sum()
    noir=retirer_pale(noir, u)
    print("  composantes pales retirees : %.1f%% de l'encre"%(100*(1-noir.sum()/max(_av,1))))
    # Depoussierage final du calque de trait.
    #
    # Premier essai : retirer les petites composantes loin d'une grosse. Mauvais
    # critere — les legendes sous les portraits n'ont aucune grosse composante,
    # leurs points sur les i n'etaient donc ancres a rien et disparaissaient :
    # « PRECIZA, KONC ZA, FACILA » devenait « PREC ZA KONC ZA FAC LA ».
    #
    # Ce qui distingue la poussiere, ce n'est pas la taille, c'est l'isolement.
    # On dilate donc l'encre : les lettres d'un meme mot se rejoignent en un
    # amas, une salissure reste seule. Un amas qui, dilatation defaite, ne pese
    # pas 1 500 pixels d'encre est de la poussiere.
    #
    # Le rayon compte autant que le seuil. A huit pixels, un mot forme un amas
    # mais une ligne n'en forme pas : « vu », « lia », « ZA », « di la » ont
    # ete pris pour des salissures et effaces. A vingt-deux, les mots d'une
    # meme ligne se rejoignent, et seule une tache vraiment seule reste seule.
    from scipy.ndimage import label as _lab, binary_dilation as _dil
    _R=22*SUR
    _amas,_na=_lab(_dil(noir, np.ones((_R,_R),bool)), np.ones((3,3),int))
    if _na:
        _encre=np.bincount(_amas[noir].ravel(), minlength=_na+1)
        _dust=np.where(_encre<1500)[0]; _dust=_dust[_dust>0]
        _seuls=np.isin(_amas,_dust) & noir
        noir &= ~_seuls
        print("  amas de poussiere retires :", len(_dust))

    # Second depoussierage, plus fin.
    #
    # Le rayon de vingt-deux pixels est genereux : une salissure posee a dix
    # pixels d'un mot rejoint son amas et survit. Il en restait une cinquantaine,
    # bien visibles dans les blancs de la page. On ne peut pas simplement
    # resserrer le rayon — c'est ce qui effacait « vu » et « di la ».
    #
    # On dilate donc de facon anisotrope : large en largeur (les mots d'une meme
    # ligne se rejoignent), etroite en hauteur (une tache posee au-dessus d'une
    # ligne ne la rejoint pas). Puis on n'efface une composante que si les trois
    # conditions tiennent ensemble :
    #   - elle est petite (moins de 900 pixels d'encre) ;
    #   - la ligne a laquelle elle appartiendrait est pauvre en encre ;
    #   - aucune vraie lettre ne se tient a moins de douze pixels d'elle.
    # La derniere condition est un veto, jamais un motif : le point d'un i, une
    # virgule, un accent touchent presque leur lettre et sont donc epargnes,
    # meme quand leur legende n'a aucune grosse composante — c'est ce qui avait
    # fait disparaitre les points de « PRECIZA, KONCIZA, FACILA ».
    _LH,_LV,_AIRE,_ENCRE,_GROS,_LOIN = 12,6,900,1500,900,12
    _mp=np.zeros(noir.shape,bool)
    for (x0,x1,y0,y1) in BOITES:
        m=8; _mp[(max(y0-m,0))*SUR:(y1+m)*SUR,(max(x0-m,0))*SUR:(x1+m)*SUR]=True
    _T=noir & ~_mp
    _d=_dil(_T,np.ones((1,_LH*SUR),bool)); _d=_dil(_d,np.ones((_LV*SUR,1),bool))
    _am,_nb=_lab(_d,np.ones((3,3),int))
    _enc=np.bincount(_am[_T].ravel(),minlength=_nb+1)
    _l,_n2=_lab(_T,np.ones((3,3),int)); _ob=find_objects(_l)
    _ai=np.array([int((_l[_ob[i]]==i+1).sum()) for i in range(_n2)])
    _bb=np.array([(o[0].start,o[0].stop,o[1].start,o[1].stop) for o in _ob])
    _g=np.nonzero(_ai>=_GROS)[0]
    _Y0,_Y1,_X0,_X1=_bb[:,0],_bb[:,1],_bb[:,2],_bb[:,3]
    _fait=0
    for i,o in enumerate(_ob):
        if _ai[i]>=_AIRE: continue
        ys,xs=np.nonzero(_l[o]==i+1)
        if _enc[_am[o][ys[0],xs[0]]]>=_ENCRE: continue
        if len(_g):
            dy=np.maximum(0,np.maximum(_Y0[i]-_Y1[_g], _Y0[_g]-_Y1[i]))
            dx=np.maximum(0,np.maximum(_X0[i]-_X1[_g], _X0[_g]-_X1[i]))
            if np.hypot(dy,dx).min() <= _LOIN*SUR: continue
        noir[o] &= ~(_l[o]==i+1); _fait+=1
    print("  taches isolees retirees :", _fait)

    for (x0,x1,y0,y1) in BOITES:
        m=6; a,b,c,d=(max(x0-m,0))*SUR,(min(x1+m,n.shape[1]))*SUR,(max(y0-m,0))*SUR,(min(y1+m,n.shape[0]))*SUR
        z=u[c:d,a:b]
        noir[c:d,a:b]=enlever_grain(z>SEUIL_NOIR,aire_gros=18)
        gris[c:d,a:b]=enlever_grain(z>SEUIL_GRIS)
    os.makedirs(f"{ORN}/couverture",exist_ok=True)
    tracer(gris,f"{ORN}/couverture/_g.svg"); tracer(noir,f"{ORN}/couverture/_n.svg")
    fusionner(f"{ORN}/couverture/_g.svg",f"{ORN}/couverture/_n.svg",f"{ORN}/couverture/couverture.svg")
    rendre(f"{ORN}/couverture/couverture.svg",f"{ORN}/couverture/couverture-x2.png",largeur=1205*2)
    Image.fromarray((np.clip(1-n,0,1)*255).astype(np.uint8)).save(f"{ORN}/couverture/couverture-nettoyee.png")
    Image.fromarray((np.clip(1-n,0,1)*255).astype(np.uint8)).resize((1205*3,1636*3),Image.LANCZOS)\
         .save(f"{ORN}/couverture/couverture-nettoyee-x3.png")

    # --- elements de trait ---
    shutil.rmtree(f"{ORN}/trait",ignore_errors=True); os.makedirs(f"{ORN}/trait")
    mp=np.zeros(noir.shape,bool)
    for (x0,x1,y0,y1) in BOITES:
        m=8; mp[(max(y0-m,0))*SUR:(min(y1+m,n.shape[0]))*SUR,(max(x0-m,0))*SUR:(min(x1+m,n.shape[1]))*SUR]=True
    T=noir & ~mp
    # embleme
    z=T[440*SUR:640*SUR, 460*SUR:740*SUR]
    C=binary_closing(z,np.ones((9*SUR//2,9*SUR//2)))
    lab,nb=label(C); objs=find_objects(lab)
    k=max(range(nb),key=lambda i:(lab[objs[i]]==i+1).sum()); sl=objs[k]
    sub=T[440*SUR+sl[0].start-4*SUR:440*SUR+sl[0].stop+4*SUR, 460*SUR+sl[1].start-4*SUR:460*SUR+sl[1].stop+4*SUR]
    tracer(sub,f"{ORN}/trait/embleme-ido.svg")
    rendre(f"{ORN}/trait/embleme-ido.svg",f"{ORN}/trait/embleme-ido-x6.png",largeur=sub.shape[1]//SUR*6)
    # bandes de lettrage
    row=T.sum(1); bandes=[];i=0
    while i<len(row):
        if row[i]>0:
            j=i
            while j<len(row) and row[j:j+12*SUR].sum()>0: j+=1
            if j-i>8*SUR: bandes.append((i,j))
            i=j
        else: i+=1
    for k,(a,b) in enumerate(bandes):
        s=T[max(a-4*SUR,0):min(b+4*SUR,T.shape[0])]
        xs=np.where(s.sum(0)>0)[0]
        if not len(xs): continue
        s=s[:,max(xs.min()-4*SUR,0):min(xs.max()+5*SUR,s.shape[1])]
        tracer(s,f"{ORN}/trait/bande{k:02d}.svg")
        rendre(f"{ORN}/trait/bande{k:02d}.svg",f"{ORN}/trait/bande{k:02d}-x4.png",largeur=s.shape[1]//SUR*4)
    return len(bandes)
if __name__=="__main__":
    print(executer(),"bandes de lettrage")
