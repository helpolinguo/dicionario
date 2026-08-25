"""Decoupage d'une page en cellules de la grille + detection des soulignements."""
import numpy as np
from scipy.ndimage import map_coordinates
from page import analyser

CW, CH = 12, 22
ETENDRE   = False      # extension du bloc a GAUCHE : deplace l'origine, au cas par cas
ETENDRE_FORCE = 0       # elargissement force a gauche : voir restore_starts.py
PROFONDEUR_MAX = 0.56  # un filet ne se cherche pas plus bas, en interlignes.
                       # Calibre sur les 1 697 lignes relevees a l'oeil : a 0,52 on
                       # perdait 7 filets vrais et 85,2 % de plages exactes ; a 0,56,
                       # 3 manques et 89,6 %. Au-dela, les fantomes DEFIRS reviennent
                       # — 11 a 0,60, 22 a 0,64.
ETENDRE_D = False      # extension du bloc a DROITE : essayee, ecartee.
                       # Elle recupere quelques fins de ligne, mais le
                       # redecoupage qu'elle entraine fait perdre des vedettes
                       # a 145 pages. Le gain ne paie pas la casse.          # raster d'une cellule
HAUT, BAS = 0.545, 0.50   # extension verticale de la cellule, en fractions du pas

def runs_binaire(row, mini):
    out=[]; i=0; n=len(row)
    while i<n:
        if row[i]:
            j=i
            while j<n and row[j]: j+=1
            if j-i>=mini: out.append((i,j))
            i=j
        else: i+=1
    return out

def soulignements(r, lignes, pasv, pash, xg, ncol, couv_min=0.50):
    """Filets de soulignement : suites horizontales, fines et solides, sous la
    ligne de base. Le tapuscrit emploie aussi des soulignements DOUBLES : on
    releve donc toutes les rangees de filet de la bande, pas seulement la
    meilleure. Retourne (rangees, plages de colonnes, couverture)."""
    B = r > 0.32
    mini = int(round(2.2*pash))
    H, W = r.shape
    res = {}
    for k, y in lignes:
        a0=max(int(round(y-0.10*pasv)),0); a1=min(int(round(y+0.45*pasv)),H)
        prof = r[a0:a1].sum(axis=1)
        if len(prof) < 4: res[k]=(None,[],0); continue
        base = a0 + int(np.argmin(np.diff(prof))) + 1
        cands=[]
        for yy in range(base+1, min(base+int(round(0.30*pasv))+2, H)):
            # Un filet appartient a la zone de sa PROPRE ligne de base.
            #
            # Les capitales de la notation DEFIRS — D, E, F, I, R, S — ont
            # toutes un empattement superieur plat. Mises bout a bout, leurs
            # sommets s'alignent en une barre horizontale continue, qui tombe
            # dans la fenetre de recherche de la ligne PRECEDENTE. La detection
            # la prenait pour un soulignement et la rapportait a la ligne du
            # dessus : « sur » dans alineo, « lego » dans abrogar, « ta » de
            # Voltaire dans anakoluto, « kun » dans amazono.
            #
            # Premier remede, ecarte : exiger du blanc SOUS le filet. Il partait
            # d'une observation juste — sous un vrai filet il n'y a rien, sous
            # un haut de lettres il y a la lettre — mais il confondait un
            # jambage avec un corps de lettre. Le « j » de « injektar » descend
            # sous son propre soulignement : le filet y etait ampute a mi-mot.
            # Il l'etait sur **2 235 plages, dans 533 pages**.
            #
            # Le bon depart est geometrique, et il ne se laisse pas tromper par
            # un jambage : ce n'est pas la profondeur d'une rangee, c'est la
            # profondeur de la PREMIERE. Un vrai filet commence entre 0,32 et
            # 0,48 interligne sous la ligne de base — mesure sur alineo,
            # informar, injektar, anakoluto. Un faux n'apparait qu'a partir de
            # 0,55, puisqu'il appartient a la ligne d'en dessous. On arrete
            # donc la recherche a 0,52.
            if (yy - y) > PROFONDEUR_MAX*pasv: break
            rs=[(a,b) for a,b in runs_binaire(B[yy], 3) if r[yy, a:b].mean() > 0.40]
            # Le ruban s'use : un filet se coupe sur une ou deux cellules sans
            # cesser d'etre un filet. On recolle les morceaux separes de moins
            # d'une cellule avant d'appliquer la longueur minimale.
            fus=[]
            for a,b in rs:
                if fus and a-fus[-1][1] <= 0.9*pash: fus[-1]=(fus[-1][0], b)
                else: fus.append((a,b))
            rs=[(a,b) for a,b in fus if b-a >= mini]
            tot=sum(b-a for a,b in rs)
            if tot: cands.append((tot, yy, rs))
        if not cands: res[k]=(None,[],0); continue
        tmax=max(c[0] for c in cands)
        retenus=[c for c in cands if c[0] >= 0.35*tmax]
        rangees=[c[1] for c in retenus]
        plages=set()
        for tot,yy,rs in retenus:
            for a,b in rs:
                if B[yy, a:b].mean() < 0.80: continue
                # Une cellule est souligne si le filet en couvre assez.
                # C'est la mesure directe, cellule par cellule : elle evite
                # d'arrondir les extremites au jugé et de faire deborder le
                # filet sur le point final ou sur le mot suivant.
                #
                # Le seuil etait a 60 %. Trop strict aux extremites : le bord
                # gauche du filet d'une vedette est la ou le ruban attaque, et
                # son empreinte y est courte. Sous « espino », la premiere
                # cellule etait couverte a 59,9 % — elle tombait, le filet
                # commencait alors au milieu du mot, et generate.py jetait le
                # soulignement entier de la vedette. Huit vedettes d'affilee y
                # sont passees a la page 155. A 50 %, le compte est bon.
                j0=int(np.floor((a-xg)/pash))-1; j1=int(np.ceil((b-xg)/pash))+1
                dedans=[]
                for j in range(max(j0,0), min(j1+1, ncol)):
                    g=xg+j*pash; d=g+pash
                    couv=(min(b,d)-max(a,g))/pash
                    if couv >= couv_min: dedans.append(j)
                if not dedans: continue
                # on ne garde que des suites contigues
                deb=dedans[0]; prev=dedans[0]
                for j in dedans[1:]+[None]:
                    if j is None or j!=prev+1:
                        plages.add((deb, prev)); deb=j if j is not None else 0
                    prev=j if j is not None else prev
        # fusion des plages qui se recouvrent
        pl=sorted(plages); fus=[]
        for a,b in pl:
            if fus and a<=fus[-1][1]+1: fus[-1]=(fus[-1][0], max(fus[-1][1],b))
            else: fus.append((a,b))
        res[k]=(rangees, fus, tmax)
    return res

def _phase_locale(pv, x0, x1, p):
    """Phase de la composante de Fourier de periode p sur [x0,x1]."""
    x = np.arange(x0, x1); s = pv[x0:x1] - pv[x0:x1].mean()
    w = 2*np.pi/p
    return np.arctan2((s*np.sin(w*x)).sum(), (s*np.cos(w*x)).sum())

def raffiner_pas(r, bloc, pash, xg, tours=4):
    """Affine (pas, phase). Deux etapes :

    1. minimisation de l'encre tombant sur les frontieres de cellule ;
    2. correction de la derive : la phase locale est mesuree par fenetres en
       travers du bloc ; si elle derive lineairement, le pas est faux, et la
       pente donne exactement la correction. C'est ce qui redresse les pages
       photographiees a une autre echelle.
    """
    y0,y1,x0,x1 = bloc
    pv = r[y0:y1+1].sum(axis=0)
    n = len(pv)
    best=(None,pash,xg)
    for p in np.linspace(pash*0.97, pash*1.03, 241):
        for ph in np.linspace(0, p, 40, endpoint=False):
            idx = np.clip(np.round(np.arange(ph, n, p)).astype(int), 0, n-1)
            s = pv[idx].mean()
            if best[0] is None or s < best[0]: best=(s,p,ph)
    p, ph = best[1], best[2]
    L = x1-x0
    if L > 12*p:
        for _ in range(tours):
            W = max(int(10*p), 60); pas_f = max(W//2, 1)
            cs=[]; phs=[]
            for a in range(x0, x1-W, pas_f):
                seg = pv[a:a+W]
                if seg.max() <= 0: continue
                cs.append(a+W/2); phs.append(_phase_locale(pv, a, a+W, p))
            if len(cs) < 4: break
            cs=np.array(cs); phs=np.unwrap(np.array(phs))
            A=np.vstack([cs, np.ones(len(cs))]).T
            pente,_ = np.linalg.lstsq(A, phs, rcond=None)[0]
            if not np.isfinite(pente) or abs(pente) < 1e-7: break
            inv = 1.0/p - pente/(2*np.pi)
            if inv <= 0: break
            p2 = 1.0/inv
            if abs(p2-p) > 0.05*p: break
            p = p2
        # rephasage sur le pas corrige
        meil=(None, ph)
        for phi in np.linspace(0, p, 200, endpoint=False):
            idx = np.clip(np.round(np.arange(phi, n, p)).astype(int), 0, n-1)
            s = pv[idx].mean()
            if meil[0] is None or s < meil[0]: meil=(s, phi)
        ph = meil[1]
    return p, ph

def extraire(chemin, garder_image=False):
    d = analyser(chemin)
    r = d['norm']; pasv=d['pasv']; pash=d['pash']; xg=d['xg']
    pash, xg = raffiner_pas(r, d['bloc'], pash, xg)
    H, W = r.shape
    xg = xg % pash                       # origine du lattis ramenee au bord gauche
    ncol = int(np.floor((W - xg)/pash))
    sou = soulignements(r, d['lignes'], pasv, pash, xg, ncol)
    # image sans soulignement : ouverture morphologique horizontale sur la bande du filet
    # rc : copie SANS les filets de soulignement. Elle ne sert qu'a decider quelles
    # cellules sont occupees et ou commence la colonne 0 ; les cellules livrees au
    # regroupement gardent leur soulignement (controle croise du releve des filets).
    from scipy.ndimage import grey_opening
    rc = r.copy()
    for k,(rangees,plages,tot) in sou.items():
        if not rangees or not plages: continue
        t0=max(min(rangees)-2,0); t1=min(max(rangees)+3,H)
        if t1-t0 < 1: continue
        for c0,c1 in plages:
            a=max(int(round(xg+c0*pash))-3,0); b=min(int(round(xg+(c1+1)*pash))+3,W)
            bande = rc[t0:t1, a:b]
            # Un filet est une structure horizontale longue : l'ouverture le
            # retient. Mais un jambage (g, p, q, y, j) le traverse ; on le
            # conserve la ou il y a de l'encre juste au-dessus ET juste en
            # dessous de la bande, sinon on eventre les lettres.
            filet = grey_opening(bande, size=(1,19))
            dessus = rc[max(t0-2,0):t0, a:b].max(axis=0) if t0>0 else np.zeros(b-a, np.float32)
            dessous = rc[t1:min(t1+2,H), a:b].max(axis=0) if t1<H else np.zeros(b-a, np.float32)
            traverse = (dessus > 0.30) & (dessous > 0.30)
            oté = np.clip(bande - filet, 0, 1)
            oté[:, traverse] = bande[:, traverse]
            rc[t0:t1, a:b] = oté
    # Decalage horizontal propre a chaque ligne. Le papier est gondole : la
    # phase de la grille glisse d'une ligne a l'autre, parfois d'un tiers de
    # cellule en bas de page. On la reprend ligne par ligne, a pas constant.
    def phase_ligne(y):
        i0=max(int(round(y-0.45*pasv)),0); i1=min(int(round(y+0.45*pasv)),H)
        if i1-i0 < 4: return 0.0
        pv=r[i0:i1].sum(axis=0)
        if pv.max() <= 0: return 0.0
        n=len(pv); meil=(None,0.0)
        for dxx in np.linspace(-0.45*pash, 0.45*pash, 37):
            idx=np.clip(np.round(np.arange(xg+dxx, n, pash)).astype(int),0,n-1)
            s_=pv[idx].mean()
            if meil[0] is None or s_ < meil[0]: meil=(s_,dxx)
        return meil[1]
    decal = np.array([phase_ligne(y) for k,y in d['lignes']])

    # extraction des cellules
    ky = np.array([y for k,y in d['lignes']])
    kk = np.array([k for k,y in d['lignes']])
    fy = (np.arange(CH)+0.5)/CH*(HAUT+BAS)*pasv - HAUT*pasv
    fx = (np.arange(CW)+0.5)/CW*pash
    nl = len(ky)
    Y = (ky[:,None,None,None] + fy[None,None,:,None] + 0*fx[None,None,None,:])
    X = (xg + decal[:,None,None,None] + np.arange(ncol)[None,:,None,None]*pash
         + fx[None,None,None,:] + 0*fy[None,None,:,None])
    Y = np.broadcast_to(Y,(nl,ncol,CH,CW)).ravel()
    X = np.broadcast_to(X,(nl,ncol,CH,CW)).ravel()
    # rz : les rangees du filet sont simplement mises a blanc, sans ouverture.
    # C'est cette version qui sert a decider si une cellule est occupee : elle
    # ne peut pas amputer une lettre, alors que rc le peut.
    rz = r.copy()
    for k,(rangees,plages,tot) in sou.items():
        if not rangees or not plages: continue
        t0=max(min(rangees)-1,0); t1=min(max(rangees)+2,H)
        for c0,c1 in plages:
            a=max(int(round(xg+c0*pash))-3,0); b=min(int(round(xg+(c1+1)*pash))+3,W)
            rz[t0:t1, a:b]=0.0
    cells = map_coordinates(r,  [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    nues  = map_coordinates(rc, [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    horsf = map_coordinates(rz, [Y,X], order=1, mode='constant', cval=0.0).reshape(nl,ncol,CH,CW)
    # renumerotation : colonne 0 = premiere colonne encree de la page
    # Une cellule est occupee si elle porte assez d'encre ET si cette encre
    # n'est pas une simple bavure du caractere voisin. Le critere de bavure
    # (encre plaquee contre le bord de la cellule) est calibre sur les cas
    # releves a la main ; il permet d'abaisser le seuil d'encre a 5 pixels,
    # ce qui rattrape les points finaux tres pales.
    plat = horsf.reshape(nl, ncol, -1)
    encre = (plat > 0.35).sum(-1)
    somme = plat.sum(-1)
    bordg = horsf[:,:,:,:2].sum((2,3)) + horsf[:,:,:,-2:].sum((2,3))
    partbord = bordg/(somme+1e-6)
    bavure = (partbord > 0.55) | ((somme < 12) & (partbord > 0.25))
    occ = (encre >= 5) & ~bavure
    frac = occ.mean(axis=0)
    # une colonne occupee sur presque toutes les lignes au bord de la page est
    # l'ombre du bord du papier, pas une colonne de texte : on la retranche.
    bord = frac >= 0.98
    use = occ.sum(axis=0) >= 3
    idx = np.where(use)[0]
    if len(idx):
        g, dte = int(idx.min()), int(idx.max())
        while g < dte and bord[g]: g += 1          # ombre du bord gauche
        while dte > g and bord[dte]: dte -= 1      # ombre du bord droit
        while g < dte and not use[g]: g += 1
        while dte > g and not use[dte]: dte -= 1
        # Le bloc est cerne par les colonnes occupees sur au moins trois
        # lignes. C'est robuste au bruit, mais cela ampute les colonnes qu'une
        # seule ligne atteint : page 6, « donacinti » est le seul mot a
        # toucher la marge, et il devenait « acinti ».
        #
        # Etendre le bloc a toute colonne encree corrige ce cas — mais
        # destabilise le lattis ailleurs : huit pages du corps y ont perdu
        # toutes leurs vedettes, le texte revenant entrelace. L'extension est
        # donc au cas par cas, activee par le drapeau ci-dessous pour les
        # seules pages ou elle est sans danger : les liminaires, ou le texte
        # est clairsemé et où il n'y a pas de vedette a perdre.
        use1 = occ.sum(axis=0) >= 1
        # A DROITE, l'extension est sans danger : elle n'ajoute des colonnes
        # qu'apres les autres, sans deplacer l'origine — la numerotation des
        # colonnes ne bouge pas, donc aucune correction deja faite n'est
        # invalidee. Elle rend les fins de ligne que le bloc coupait :
        # « preciz », « apa », « anon ».
        if ETENDRE_D:
            while dte < ncol-1 and use1[dte+1] and not bord[dte+1]: dte += 1
        # A GAUCHE, elle deplace l'origine et decale tout : elle a fait perdre
        # a huit pages du corps toutes leurs vedettes. Reservee, par le drapeau
        # ci-dessous, aux pages ou le texte est clairseme et sans vedette.
        if ETENDRE:
            while g > 0 and use1[g-1] and not bord[g-1]: g -= 1
        # Elargissement FORCE a gauche, sans condition d'usage. La regle
        # ci-dessus veut qu'une colonne serve sur plusieurs lignes ; or la
        # premiere lettre d'une vedette commencee une cellule trop tot est
        # souvent seule dans sa colonne — « sorgumo », « jorno ». Elle ne
        # declenche donc rien. Ce drapeau n'est utilise que par
        # restore_starts.py, qui recoupe en memoire et ne touche pas au corpus :
        # ce qu'il ramene de trop est ecarte ensuite par le filtre de bavures
        # et par le decodage, qui doit rendre un vrai caractere.
        if ETENDRE_FORCE:
            g = max(0, g - int(ETENDRE_FORCE))
        c0, cmax = g, dte
    else:
        c0, cmax = 0, ncol-1
    cells = cells[:, c0:cmax+1]; nues = nues[:, c0:cmax+1]; occ = occ[:, c0:cmax+1]
    ncol = cells.shape[1]
    kk = kk - kk.min()
    sou = {k:(yy,[(a-c0,b-c0) for a,b in pl],t) for k,(yy,pl,t) in sou.items()}
    out = dict(pasv=pasv, pash=pash, xg=xg, col0=c0, angle=d['angle'], bloc=d['bloc'],
               lignes=list(zip(kk.tolist(), ky.tolist())), ncol=ncol, decal=decal,
               cells=cells, nues=nues, occ=occ, sou=sou, shape=(H,W))
    if garder_image: out['norm']=r; out['nettoye']=rc
    return out
