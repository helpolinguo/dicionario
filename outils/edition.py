# -*- coding: utf-8 -*-
"""Extraction d'une base lexicale structuree a partir du tapuscrit decode.

Le tapuscrit suit une grammaire stricte, qui se lit dans la mise en page :

    vedetto. (fako.) Senco unesma. - II. Senco duesma. - L. nomo latina. - DEFIS.
    ^^^^^^^  ^^^^^^                    ^^^                ^^^^^^^^^^^^^   ^^^^^
    soulignee, colonne 0                sens               nomo cientifika  lingui

Chaque enregistrement porte sa **provenance** — image du scan, page du livre,
ligne de la grille — et ses **drapeaux de qualite**. Rien n'est efface : ce qui
est douteux est signale, pas masque.
"""
import numpy as np, os, pickle, re, collections, sys, json, os, unicodedata
sys.path.insert(0,'/root/dicionario/outils')
from consolider import vedettes
T="/root/dicionario/travail"
DECALAGE_FOLIO = 7          # numero de page du livre = index d'image - 7

LANGUI = {'D':'Germana','E':'Angla','F':'Franca','I':'Italiana','R':'Rusa',
          'S':'Hispana','L':'Latina','P':'Portugalana','G':'Greka','N':'Nederlandana'}
# Certaines notations epellent la langue : « FDSued » = Franca, Germana, Sueda.
ABREV = {'Sued':'Sueda','Ned':'Nederlandana','Pol':'Polona','Dan':'Dana',
         'Nor':'Norvegana','Fin':'Finlandana','Cek':'Cheka'}
# Quelques notations epellent la langue au long, separees par des virgules —
# « Jap.,Sanskr. » pour « ka(d) ». Elles n'entrent pas dans le code a lettres :
# lues comme du texte, l'article passait pour « sen-lingua ».
EPELE = {'Jap':'Japoniana','Sanskr':'Sanskrita','Hebr':'Hebrea','Arab':'Araba',
         'Turk':'Turka','Chin':'Chiniana','Malay':'Malaya','Skand':'Skandinava',
         'Gr':'Greka','Lat':'Latina','Slav':'Slava','Hind':'Hindua'}
RE_EPELE = re.compile(r'(?:[-\u2013]|^)\s*((?:[A-Z][a-z]{1,7}\.?\s*,\s*)+[A-Z][a-z]{1,7}\.?)\s*$')

def _lire_code(jeton):
    """Le jeton final est-il un code de langues ? Retourne la liste, ou None.

    Le discriminant est la CASSE : un code est en capitales. Sans elle, tout mot
    terminant une phrase — « gamo », « radii », « korpo » — passait pour un code.
    On tolere une capitale abimee par le decodage (« dEFIRS ») et le « l » lu
    pour « I » (« DEFlS »), mais on exige que le jeton soit majoritairement haut
    de casse.
    """
    if not jeton or len(jeton) > 12: return None
    hauts=sum(1 for c in jeton if c.isupper())
    if hauts < max(1, int(0.6*len(jeton))): return None
    out=[]; reste=jeton
    for ab,nom in ABREV.items():                    # abreviation epelee, en fin
        if reste.endswith(ab): out.append(nom); reste=reste[:-len(ab)]; break
    for c in reste.upper().replace('L','I') if False else reste:
        c = 'I' if c=='l' else c.upper()
        if c not in LANGUI: return None
        out.append(LANGUI[c])
    # Aucun vrai code ne nomme deux fois la meme langue. « II » et « III » sont
    # des numeros de sens que la fin d'article laisse pendre — chez « forsan »,
    # « xenio », « -ajo », « ek » —, et l'edition les donnait pour « Italiana,
    # Italiana ». Le decoupage en articles (dividar) posait deja cette regle ;
    # elle vaut ici aussi.
    if len(set(out)) != len(out): return None
    return out or None
# Le code de langues est parfois colle au point qui le precede — « agar
# lo.DEFIS. » — faute de l'original. On accepte donc le point comme separateur
# au meme titre que le tiret.
# Le code final n'est pas toujours precede d'un tiret : il se colle au point
# — « agar lo.DEFIS. » — ou a la parenthese fermante — « (anke metaf.)DEFIRS ».
# Il n'est pas toujours suivi d'un point non plus.
RE_CODE   = re.compile(r'(?:[-–.)]|^)\s*([DEFIRSLP]{1,8})\s*[.,]?\s*$')
# La parenthese ouvrante manque parfois dans l'original : « abduktar.-trans.) »
# se lit ainsi au scan, verifie. On tolere donc son absence, mais seulement si
# rien n'est deja ouvert et si le contenu est court, pour ne pas avaler une
# phrase entiere. Le point qui suit la parenthese fermante est consomme : sans
# cela la definition commencait par « . » — « ablegato », « abulio ».
RE_FAKO   = re.compile(r'^\(([^()]{1,40})\)\s*\.?\s*')
RE_FAKO2  = re.compile(r'^([^()]{1,25})\)\s*\.?\s*')
# Le nom scientifique est annonce par « L. ». Le tiret qui le precede manque
# souvent : « ... kompozaji". L. artemisia absinthium ». On accepte donc le
# point et le debut de segment au meme titre que le tiret.
# La virgule appartient au nom scientifique quand il donne deux formes —
# « L. anas, anatis ». Sans elle dans la classe, le nom restait dans le sens.
# La SECONDE forme peut faire plusieurs mots — « L. rubus caesius, rubus
# fructicosus » chez rovo, « L. dalbergia nigra, jacarania mimosifolia » chez
# palisandro, et jusqu'a la glose de l'auteur, « L. conium maculatum, e speco di
# cicuta » chez cikuto. N'en prendre qu'un laissait le reste dans la definition,
# precede de la virgule orpheline du nom : « ... (rovbero). , rubus
# fructicosus ». On admet donc la seconde forme entiere, quatre mots comme la
# premiere.
# Le nom scientifique ne finit pas toujours sur un tiret ou en fin de segment :
# il est souvent suivi d'une parenthese fermante — « (L. triticum caninum) » —
# d'une virgule qui reprend la phrase, ou du numero du sens suivant —
# « L. aquila II. ». Ancre sur le seul tiret, il restait dans la definition de
# soixante-sept articles. On borne donc le nom par sa FORME — quatre mots
# latins au plus, plus une seconde forme apres virgule pour « anas, anatis » —
# au lieu de le borner par ce qui le suit.
# Le point du « L. » manque parfois — « ...puteo-kordegi.- L tilia. - FISL. »
# chez tilio. On l'admet sans son point, mais alors seulement devant une
# MINUSCULE : « - La persono qua... », « - Longa bastono... » ouvrent une
# definition, et le L y prendrait la premiere lettre du mot.
# Le nom se termine souvent sur « .- » sans espace — « L. viverra genetis.- II.
# (tekn.) ... » chez jineto. Sans le tiret dans la classe qui suit le point, le
# nom restait dans la definition de soixante-huit articles.
# Un « L. » qui introduit un EXEMPLE n'annonce pas le nom scientifique de
# l'article : « enklitiko. ... Kom ex.: L. que en neque ; ne en venisne ; F. ce
# en est-ce ». Pris pour un binome, il quittait la definition — qui restait sur
# « Kom ex.; » — pour aller s'afficher en nom latin de l'article. Le « F. » qui
# suit, lui, n'a jamais ete pris : seul le « L. » preteait a confusion.
RE_LATINA = re.compile(
    r'(?:(?<!ex\.)[-–.(,;:]|^)\s*(?:L\.\s*|L\s+(?=[a-z]))'
    r'([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}'
    r'(?:\s*,\s*[A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3})?)'
    r'\s*(?=[-–)(:;,]|\.[\s)–-]|\.?$|\s(?:I{1,3}|IV|VI{0,3})\.)')
# Les sens se separent par « - II. », mais le tiret manque souvent : « ...
# komenco-punto e fino-parto. II. (gram.) ... ». On coupe donc aussi sur un
# point suivi du numero de sens, ce qui vaut pour 107 articles.
# Six articles numerotent leurs sens en chiffres ARABES — « grapino »,
# « kapelo », « koliaro », « kondamnar », « konfliktar » — et « iambo » melange
# les deux niveaux. Sans cette branche, tout leur contenu restait dans un seul
# sens. On exige la majuscule ou la parenthese apres le numero, ce qui ecarte
# « 1.000 » et les formules chimiques. Le « l » lu pour « 1 » est admis : la
# confusion est constante dans ce tapuscrit.
# La parenthese FERMANTE vaut le point : « elaborar. ... per laborado. (anke
# metaf.) II. (fiziol.) Igar absorbebla... ». Le numero suit alors une
# parenthese, non un point, et le sens ne se coupait pas — onze articles
# gardaient deux sens en un. Le garde-fou tient : « pos I. K. » chez « hejiro »
# et « rejo Francisko I. » chez « legiono » ne suivent ni point ni parenthese,
# et ne se coupent pas.
# Le point du numero manque parfois : « ...di elektro-lampo. III veziketo
# produktata... » chez « ampulo », « ...kontenar aquo. – II Mar-baseno... »
# chez « baseno ». Le livre n'en compte que deux, et les deux sont de vrais
# sens ; on admet donc le numero suivi d'une simple espace, a condition qu'une
# lettre suive. Une PARENTHESE la vaut : le sens s'ouvre tres souvent sur son
# qualificatif, « reklamacar. I(netrans.) ... ne-equitatoza.II (trans.)
# Postular... », et le numero se retrouvait alors dans le texte du sens, ou il
# doublait celui que les editions posent elles-memes — « 1. I (zool.) Mamifero
# karnivora... » chez « leono ». L'espace y est facultative : la dactylo colle
# le numero a la parenthese aussi souvent qu'elle l'en separe.
# Le livre numerote jusqu'a VIII — « modo » a huit sens, « exemplo », « lineo »
# et « punto » en ont sept. La suite s'arretait a VI : « -VII.(tipogr.) » chez
# « punto » restait dans le sens VI, son numero au milieu du texte.
# « VI{0,3} » couvre V, VI, VII et VIII d'un seul tenant, comme le fait deja la
# regle qui OTE le numero en tete de sens. Le livre ne va pas au-dela : aucun
# article ne porte de IX.
RE_SENCO  = re.compile(r'\s*(?:[-–]\s*|(?<=[.)])\s*)'
                       r'(?=(?:I{1,3}|IV|VI{0,3})[.,]\s?'
                       r'|(?:I{1,3}|IV|VI{0,3})\s+[A-Za-zÀ-ÿ]'
                       r'|(?:I{1,3}|IV|VI{0,3})\s*\('
                       r'|[l\d]\d?\.\s*[A-ZÀ-Ý(])')
# L'auteur numerote parfois ses sens ENTRE PARENTHESES : « (1) ... (2) ... ».
# Ecrits ainsi, ils tiennent le plus souvent en une seule phrase — les morceaux
# se suivent apres un point-virgule ou deux-points, « (1) Garnisar ye ulo...;
# (2) Garnisar per esar pozita sur... » chez « kovrar » — et le livre les rend
# tels quels : on les laisse.
#
# Mais le PREMIER de ces numeros suit la vedette, la ou l'analyse cherche le
# domaine : il partait au champ `fako`, d'ou il etait ecarte comme numero.
# L'article perdait alors son « (1) » en gardant son « (2) » — « ramo », «
# romano », « vice », les trois seuls du livre. La numerotation orpheline ne
# renseigne plus personne ; on coupe le sens a sa place, et les editions
# renumerotent comme elles le font des autres. La coupure ne se fait qu'apres
# une phrase CLOSE, pour ne pas defaire les enumerations d'un seul souffle.
RE_ORFA_NUM = re.compile(r'(?<=[.!])\s*[-–]?\s*\((?:I{2,3}|IV|[2-9])\)\s*'
                         r'(?=[A-Za-zÀ-Ý«(])')
RE_NUM_UNESMA = re.compile(r'\(\s*(?:1|l|I)\s*\)')
FINALES_OK = ("o","a","e","i","ar","ir","or")
# Signe de coupure pose dans le texte par l'analyse, la ou un sens finit sans
# que le livre l'ait numerote — le code de langues qui le clot, par exemple.
# Invisible, il est lu par le decoupage en sens, et n'en sort jamais.
KUPO = "\ue002"

_LP=None
def _lignes_plus(fichier=f"{T}/lignes_plus.txt"):
    """Lignes de bas (ou de haut) de page perdues par une RE-COUPE ulterieure.

    La page 290 l'a montre : son extraction a ete refaite le 13 aout, et le
    nouveau bloc s'arretait quatre lignes plus haut que l'ancien. Le fac-simile,
    compose avant la re-coupe, garde ces lignes ; l'edition de lecture, batie
    sur le .npz, les avait perdues — « koklusho » finissait sur « precipue la »
    et « kokono » manquait au livre. Plutot que de re-couper la page, ce qui
    deplacerait toutes les corrections indexees par (page, ligne, colonne), on
    rend ici les lignes telles que le fac-simile les porte.

    Une ligne du fichier : page<TAB>numero de ligne<TAB>texte.
    Le texte est celui de la grille, espaces de tete comprises.
    """
    global _LP
    if _LP is None:
        _LP={}
        if os.path.exists(fichier):
            for l in open(fichier,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,v=l.split("\t")
                _LP.setdefault(int(a),{})[int(b)]=v
    return _LP


def _signaturo():
    """Empreinte des fichiers dont depend le texte decode."""
    noms=["cls_lab.npy","cls_alternatives.pkl","lignes_plus.txt",
          "exceptions_fins.txt","exceptions_ornements.txt","exceptions_paires.txt",
          "exceptions.txt","exceptions_relecture.txt","exceptions_manuel.txt",
          "pages_non_dactylo.txt"]
    sig=[]
    for n in noms:
        p=f"{T}/{n}"
        sig.append((n, os.path.getmtime(p) if os.path.exists(p) else 0))
    d=f"{T}/cellules"
    if os.path.isdir(d):
        sig.append(("cellules", max((os.path.getmtime(os.path.join(d,f))
                                     for f in os.listdir(d)), default=0)))
    return sig


def charger_texte(kash=True):
    import pickle
    kf=f"{T}/_pages.pkl"
    sig=("v2", _signaturo())
    if kash and os.path.exists(kf):
        try:
            with open(kf,"rb") as h: pages,corrigees,filetoj,vieux=pickle.load(h)
            if vieux==sig: return pages,corrigees,filetoj
        except Exception: pass
    pages,corrigees,filetoj=_charger_texte()
    try:
        with open(kf,"wb") as h: pickle.dump((pages,corrigees,filetoj,sig),h)
    except Exception: pass
    return pages,corrigees,filetoj


def _charger_texte():
    from decoder import charger, page_texte
    from generer import exceptions
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True); exc=exceptions()
    corrigees=set((p,k,c) for (p,k,c) in exc)
    pages={}; filetoj={}
    for pg in range(int(M[:,0].max())+1):
        try: lignes=page_texte(pg,lab,M,tab)
        except Exception: continue
        out=[]
        for k,s in lignes:
            l=list(s)
            # Une correction peut allonger la ligne : une vedette relue peut
            # compter plus de cellules que la lecture automatique. On complete
            # la ligne au lieu de laisser tomber la correction.
            for (pp,kk,cc),v in exc.items():
                if pp==pg and kk==k:
                    if cc>=len(l): l.extend(" "*(cc-len(l)+1))
                    l[cc]=v
            out.append((k,"".join(l).rstrip()))
        sup=_lignes_plus().get(pg)
        if sup:
            par=dict(out); par.update(sup)
            out=sorted(par.items())
        pages[pg]=out
        # Les filets de soulignement de la page, tels que le decoupage des
        # cellules les a releves : une liste de plages de COLONNES par ligne,
        # dans la meme numerotation que le texte rendu ci-dessus. C'est la
        # marque que l'auteur a portee lui-meme sur son tapuscrit ; elle
        # designe le domaine, la locution, le nom latin, le mot cite.
        try:
            z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
            import pickle as _pk
            sou=_pk.loads(z['sou'].item())
            filetoj[pg]={int(k): [(int(a),int(b)) for a,b in v[1]]
                         for k,v in sou.items() if v[1]}
        except Exception:
            filetoj[pg]={}
    return pages, corrigees, filetoj


_ND=None
def _non_dactylo():
    """Pages qui ne sont pas dactylographiees : couverture, pages blanches."""
    global _ND
    if _ND is None:
        _ND=set(); p=f"{T}/pages_non_dactylo.txt"
        if os.path.exists(p):
            for l in open(p,encoding='utf-8'):
                if l.startswith('#') or not l.strip(): continue
                _ND.add(int(l.split('\t')[0]))
    return _ND

# Un folio, tel que le decodeur le rend : « 113 », mais aussi « lOO », « 2Ol »,
# « ll2 » — le un et le zero de la machine a ecrire se lisent l et O. Deux
# folios se suivent parfois, « 173/175 », quand la page porte les deux.
RE_FOLIO=re.compile(r'^[\dlOoIi][\dlOoIi\s/.,\u2013-]{0,7}$')
# Le folio, en fin de ligne de texte, se distingue par le blanc qui le precede :
# « ... sen shancelar   563 ». Il n'appartient pas a la phrase.
RE_FOLIO_FIN=re.compile(r'\s{2,}[\dlOoIi]{1,4}[.,]?$')

def decouper(pages, corrigees, filetoj=None):
    filetoj = filetoj or {}
    ent=[]; tetoj={}
    for pg in sorted(pages):
        if pg < 8: continue          # liminaires : titre, preface, rezumo di gramatiko
        if pg in _non_dactylo(): continue   # pages blanches : rien a decouper
        try: ved={k for k,_ in vedettes(pg)}
        except Exception: ved=set()
        # Marge de la page, lue sur le TEXTE DECODE et non sur l'occupation des
        # cellules : quarante-cinq pages commencent plus a droite — la 380
        # commence en 5 — et occ() y voit de l'encre en colonne 0 la ou le
        # decodage ne voit rien. Toutes leurs entrees etaient perdues.
        lignes_pl=[s for _,s in pages[pg] if s.strip()]
        if lignes_pl:
            mg=min(len(s)-len(s.lstrip()) for s in lignes_pl)
        else:
            mg=0
        # Une vedette non soulignee reste une vedette : elle commence a la
        # marge, apres une ligne blanche, et se presente comme « mot. ».
        # Une vedette non soulignee reste une vedette. On ne lui impose pas la
        # marge : « +quoniam » est en colonne 17, « milieto » en 5. Ce qui la
        # designe, c'est de suivre une ligne blanche et de se presenter comme
        # « mot. ». Le « + » qui marque les mots non officiels en fait partie.
        # « - oz-. », « - as. », « + prei. » : la dactylo a laisse une espace
        # entre le signe et le mot. Sans cette tolerance, « -oz- » et « -as »
        # n'etaient pas des vedettes du tout et tombaient dans l'article
        # precedent.
        # « .heliko », « .hipofizo » : la dactylo a frappe un point avant le
        # mot. Sans cette tolerance, ces deux articles n'etaient pas des
        # vedettes du tout et tombaient dans le precedent — « hipofizo » se
        # lisait a la fin de « hipodromo ».
        # « "dis" », « "hidalgo" » : un emprunt cite est une vedette a part
        # entiere, et l'auteur l'entoure de guillemets. « ha ! » : une
        # interjection se termine par son point d'exclamation, non par un
        # point. « o (d). » : la vedette porte sa variante entre parentheses,
        # comme « a(d). », mais separee par une espace.
        # « rutino, » : la dactylo a frappe la VIRGULE au lieu du point. Le
        # filet est bien la, la ligne blanche aussi ; seule la ponctuation
        # manquait, et l'article entier tombait dans « ruteno », dont il
        # avalait le symbole chimique. Sur les six cent trente-neuf pages, une
        # seule ligne suit une ligne blanche en se presentant « mot, » : celle-
        # la. Admettre la virgule ne coute donc aucun faux positif.
        # « -- protestanto. » : l'auteur a marque d'un double tiret l'article
        # qu'il inserait apres coup. « +intrenar (trans.) » : il a omis le
        # point, et c'est le qualificatif entre parentheses qui clot la
        # vedette. Sans ces deux tolerances, « protestanto » tombait dans
        # « protestar » et « +intrenar » dans « intramolekula ».
        RE_VED=re.compile(r'^(?:[-–]{2}\s*)?[\"«]?\.?[+-]?\s?'
                          r'[A-Za-z][A-Za-z\'’-]{0,30}[\"»]?'
                          r'\s?-?\s?(?:\([A-Za-z]{1,3}\)\s?)?'
                          r'(?:[.!,]|\s*\([A-Za-z]{1,12}[.,)])')
        # La ligne blanche ne se lit pas dans le texte : elle N'EST PAS dans la
        # grille. page_texte() ne rend que les lignes detectees, et leurs
        # numeros sautent — 2, 3, puis 5. C'est ce SAUT qui marque le blanc.
        # A chercher une chaine vide, la regle ne se declenchait que sur la
        # premiere ligne de chaque page : la 536 ne rendait qu'un article sur
        # quatorze, et « simpla », « utila », « granda » manquaient au livre.
        # Le folio, et les lignes qui ne portent aucune lettre — les chiffres
        # en exposant d'une formule, poses au-dessus de leur ligne —, ne
        # rompent pas le blanc : ils ne sont pas du texte suivi. Sans cette
        # transparence, « smalto » (folio colle a la vedette) et « morfino »
        # (les indices de sa formule au-dessus) n'etaient pas des vedettes du
        # tout, et leurs articles tombaient hors du livre.
        prec=None; ved2=set()
        for k,s in pages[pg]:
            if not s.strip(): continue
            if RE_FOLIO.match(s.strip()) or not any(c.isalpha() for c in s):
                continue
            blanc = (prec is None) or (k - prec > 1)
            # Un mot TOUT en capitales n'est pas une vedette : c'est le code de
            # langues, que l'auteur a parfois rejete sur une ligne a part apres
            # un interligne — « DEFIR. » sous « sodo ». « Direktorio », « Usa »,
            # « Venus » gardent leur capitale initiale et restent des vedettes.
            u=s.lstrip()
            capitales = re.match(r'^[A-Z]{2,}\b', u) is not None
            if blanc and not capitales and RE_VED.match(u): ved2.add(k)
            prec=k
        # Les indices d'une formule, frappes sur une ligne a part JUSTE AVANT
        # la vedette qui les porte : « 12  22  11 » au-dessus de « laktoso ».
        # La machine ne descend pas les chiffres ; la dactylo remonte donc la
        # ligne. Quatre formules du livre sont dans ce cas — laktoso, morfino,
        # saponino, fenacetino — et leur ligne d'indices se rattachait a
        # l'article PRECEDENT, ou elle n'a rien a faire. Meme sort pour le
        # point isole qui precede « deciliono ».
        contenu=[(k,x) for k,x in pages[pg] if x.strip()]
        muta=set()
        for i,(k,x) in enumerate(contenu):
            if any(c.isalpha() for c in x): continue
            j=i+1
            if j < len(contenu) and (contenu[j][0] in ved or contenu[j][0] in ved2):
                muta.add(k)
        cur=None; orfa=[]
        for k,s in pages[pg]:
            if not s.strip() or k in muta: continue
            if k in ved or k in ved2:
                if cur: ent.append(cur)
                cur=dict(image=pg, pagino=pg-DECALAGE_FOLIO, ligno=k, lineoj=[(k,s)])
            elif cur is not None:
                cur['lineoj'].append((k,s))
            elif not RE_FOLIO.match(s.strip()):
                orfa.append((k, RE_FOLIO_FIN.sub('', s)))
        if cur: ent.append(cur)
        if orfa: tetoj[pg]=orfa
    # Article commence en bas d'une page et poursuivi en tete de la suivante.
    # « tamburo » (folio 567) s'arretait sur « kovrita ye » : ses deux dernieres
    # lignes ouvrent la page 568, avant « tamburino », et le decoupage, qui
    # repart de zero a chaque page, les jetait. On ne les rattache que si
    # l'article precedent est reste EN SUSPENS — sans code de langues finale —,
    # ce qui est la marque meme de la coupure.
    RE_KODO=re.compile(r'[-–]\s*[A-Za-z]{1,12}\.?\s*$')
    der={}
    for i,e in enumerate(ent):
        if e['ligno'] >= der.get(e['image'], (-1,-1))[0]: der[e['image']]=(e['ligno'], i)
    n_suite=0
    for pg,lignes in sorted(tetoj.items()):
        d=der.get(pg-1)
        if d is None: continue
        e=ent[d[1]]
        t=" ".join(x for _,x in e['lineoj']).strip()
        # L'article precedent porte deja son code : il est clos, la tete de
        # page ne le prolonge pas.
        if RE_KODO.search(t): continue
        # Il se termine sur un tiret seul : ce n'est pas la phrase qui manque,
        # c'est le code de langues. « "nirvana" » finit ainsi, et la tete de la
        # page suivante appartient a « nivar », article que le livre a perdu.
        if re.search(r'[-–]\s*$', t): continue
        u=" ".join(x.strip() for _,x in lignes).strip()
        # Une lettre esseulee, un signe : un accident de frappe, non un texte.
        if len(u) < 8 or len(u.split()) < 2: continue
        e['lineoj'].extend(lignes); n_suite+=1
    if n_suite: print("articles poursuivis en tete de page : %d"%n_suite)
    for e in ent:
        e['korektita'] = sum(1 for (k,_) in e['lineoj']
                             for c in range(120) if (e['image'],k,c) in corrigees)
        e['filetoj'] = filetoj.get(e['image'], {})
    return ent


def sublineajoj(e):
    """Ce que l'auteur a SOULIGNE dans l'article, remis bout a bout.

    Le tapuscrit n'a pas d'italique : la dactylo souligne. Elle souligne le
    mot-vedette, le nom latin, le domaine — « (matem.) » — et la locution qui
    porte sa propre definition — « Proporciono geometriala : ... ». Le releve
    des filets donne, ligne par ligne, des plages de colonnes ; il suffit d'y
    lire le texte.

    Une locution coupee en fin de ligne se recolle : « Proporciono geome- »
    puis « triala ». Le trait d'union est celui de la coupure, non du mot.
    """
    fil=e.get('filetoj') or {}
    par={k:s for k,s in e['lineoj']}
    morceaux=[]                       # (texte, coupe_a_la_fin)
    for k,s in e['lineoj']:
        fin=len(s.rstrip())
        for a,b in sorted(fil.get(k, [])):
            if a >= len(s): continue
            t=s[a:b+1]
            # Le filet mord parfois sur la ponctuation voisine.
            t=t.strip(" .,;:)(\u00ab\u00bb\"'")
            if not t: continue
            # Coupure de fin de ligne : le trait d'union suit immediatement.
            coupe = s[b+1:fin].strip() == '-'
            morceaux.append((t, coupe))
    out=[]; i=0
    while i < len(morceaux):
        t,coupe = morceaux[i]
        while coupe and i+1 < len(morceaux):
            i += 1
            t = t + morceaux[i][0]
            coupe = morceaux[i][1]
        out.append(t); i += 1
    # Le mot-vedette est souligne comme le reste : il n'apprend rien ici.
    v=(e.get('vedetto') or '').lower().lstrip('*+')
    vu=set(); res=[]
    for t in out:
        u=re.sub(r'\s+',' ',t).strip()
        if len(u) < 3 or u.lower().rstrip('.') == v: continue
        if u.lower() in vu: continue
        vu.add(u.lower()); res.append(u)
    return res

_FIN=("ar","ir","or","as","is","os","us","o","a","e","i")
def _atteste(w, lexique):
    """Le mot, ou sa racine une fois la finale grammaticale otee, est-il vedette ?"""
    if not lexique or not w: return False
    w=w.lower()
    if w in lexique: return True
    for f in _FIN:
        if w.endswith(f) and len(w)-len(f)>=2 and w[:-len(f)] in lexique: return True
    return False

def recoller(lignes, lexique=None):
    """Recolle les lignes d'un article en rendant les mots coupes en fin de ligne.

    Le tapuscrit coupe les mots au bord droit : « por rezis- » puis « tar ».
    Les joindre par une espace donnait « rezis- tar ». On les recolle donc sans
    espace et sans le trait.

    Un compose qui tombe pile sur la coupure est ambigu — « homo-korpo » coupe
    apres le trait devrait garder son trait. On tranche par le lexique : si le
    On teste le mot RECOLLE, non le fragment de gauche. La premiere version
    testait la gauche : « re », « pro », « kom », « fa », « mi » sont des
    prefixes, donc toujours attestes comme vedettes, et le trait restait —
    « re-cevar », « pro-duktita », « kom-batis » sortaient coupes en deux. Le
    jugement lexical de la premiere vague n'a quasiment trouve que cela.
    """
    out=""
    for i,s in enumerate(lignes):
        s=s.strip()
        if not out: out=s; continue
        if out.endswith('-') and s[:1].islower() and out[:-1][-1:].isalpha():
            gauche=re.split(r'[^A-Za-z’\'-]', out[:-1])[-1]
            droite=re.split(r'[^A-Za-z’\'-]', s)[0]
            if _atteste(gauche+droite, lexique):
                out=out[:-1]+s          # le mot recolle existe : c'etait une cesure
            elif (lexique and _atteste(gauche, lexique)
                          and _atteste(droite, lexique)):
                out=out+s               # deux mots attestes : compose, on garde le trait
            else:
                out=out[:-1]+s          # dans le doute, la cesure est le cas courant
        else:
            out=out+" "+s
    return out

# Deux articles frappes a la suite sur une meme ligne. Le decoupage se fait sur
# la ligne blanche qui precede la vedette ; quand la dactylo n'en a pas laisse,
# le second article se retrouve avale dans la definition du premier —
# « cerebelo » dans « cereala », « asepta » dans « asentar ». Ce qui les separe
# est sur : chaque article FINIT par son code de langues. Tout ce qui suit
# « - DEFIS. » et se presente comme « mot : » ou « mot. » est donc un article
# neuf. On exige un vrai code — « L. » (nom latin) et « Simb. » (symbole
# chimique) n'en sont pas — pour ne pas couper « - L. saponaria. » en deux.
RE_DIVIDO = re.compile(r'[-–]\s*([A-Za-z]{1,12})\.\s+'
                       r'(?=(?:[+*]?[a-zà-ÿ][a-zà-ÿ\'\u2019-]{1,25}'
                       r'(?:\s*[:.!]\s|\s+\()'
                       # Emprunt cite pris pour vedette : « "argus" », « "inch" ».
                       # Onze articles se trouvaient ainsi noyes dans leur voisin.
                       r'|["\u00ab]\s*[+*]?[a-zà-ÿ]))')

_DIVIDI=None
def _dividi(fichier=f"{T}/dividi.txt"):
    """Coupures relevees a l'oeil : image:ligno -> chaine ou couper.

    Le reperage automatique s'appuie sur le code de langues qui finit chaque
    article. Quand une note s'est glissee entre les deux — « shokar. ... II.
    (Ref. "Adjuntenda", fine di ca verko) shovar. (trans.) Glitigar per
    pulso. - DE. » —, il n'y a plus de code a l'endroit de la couture, et le
    second article — une racine entiere, absente du reste du livre — restait
    noye dans le premier.
    """
    global _DIVIDI
    if _DIVIDI is None:
        _DIVIDI={}
        if os.path.exists(fichier):
            for l in open(fichier,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                p=l.split("\t")
                if len(p)>=2 and p[0].strip() and p[1].strip():
                    _DIVIDI[p[0].strip()]=p[1].strip()
    return _DIVIDI


def dividar(brut, lexique=None):
    """Scinde les entrees qui en contiennent deux. Rend la liste elargie."""
    out=[]
    for e in brut:
        t = e.get('teksto_brut')
        if t is None:
            t = re.sub(r'\s+',' ',recoller([s for _,s in e['lineoj']], lexique)).strip()
            # La couche de correction du texte brut doit s'appliquer AVANT le
            # decoupage : c'est elle qui retablit le point du code de langues,
            # sur lequel la coupure s'appuie (« - DEFIR. shut! »).
            for a,b in _texti().items():
                if a in t: t=t.replace(a,b)
        # La coupure relevee a l'oeil passe la premiere : elle porte la ou le
        # code de langues manque, et le reperage automatique ne voit rien.
        _c = _dividi().get("%d:%d" % (e.get('image',-1), e.get('ligno',-1)))
        if _c and _c in t and t.index(_c) > 0:
            j=t.index(_c)
            f=dict(e); f['teksto_brut']=t[:j].strip()
            f['drapeli_pre']=['artiklo-dividita']
            out.append(f)
            t=t[j:].strip()
        while True:
            coupe=None
            for m in RE_DIVIDO.finditer(t):
                j=m.group(1)
                # « - II. » n'est pas un code mais un numero de sens : lu comme
                # « Italiana, Italiana », il coupait « seniora » en deux. Aucun
                # vrai code ne repete une langue.
                if j=='L' or len(set(j.upper()))!=len(j): continue
                # « - S. stachys. » : ce qui suit le code est le nom latin de la
                # plante, pas un article. Un article a une definition.
                # Un article peut etre tres bref : « "kilowatt". 1000 "watt" »
                # tient en vingt-trois signes. Le seuil ecarte surtout le nom
                # latin isole, plus court encore.
                if len(t)-m.end() < 18: continue
                if _lire_code(j):
                    coupe=m; break
            if not coupe: break
            f=dict(e); f['teksto_brut']=t[:coupe.end()].strip()
            f['drapeli_pre']=['artiklo-dividita']
            out.append(f)
            t=t[coupe.end():].strip()
        f=dict(e); f['teksto_brut']=t
        if out and out[-1].get('image')==e.get('image') and out[-1].get('ligno')==e.get('ligno'):
            f['drapeli_pre']=['artiklo-dividita']
        out.append(f)
    return out

_TEXTI=None
def _texti(fichier=f"{T}/texti.txt"):
    """Corrections du TEXTE BRUT, avant toute analyse.

    Certaines fautes doivent se reparer avant que le code de langues, le
    domaine et les sens soient lus — sinon la reparation arrive trop tard.
    Ainsi « autoritato » : l'auteur a ajoute « pensala. » en marge, tres a
    droite, pour completer « verko » a la ligne suivante ; le mot s'est
    retrouve APRES le « - DEFIRS. » de l'article precedent, dont le code ne
    s'ancrait donc plus en fin de chaine.
    """
    global _TEXTI
    if _TEXTI is None:
        _TEXTI={}
        if os.path.exists(fichier):
            for l in open(fichier,encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                p=l.split("\t")
                if len(p)>=2 and p[0].strip(): _TEXTI[p[0].strip()]=p[1].strip()
    return _TEXTI

def _kupar(x):
    """Coupe la queue d'un segment, SANS toucher a l'ellipse finale.

    L'auteur marque d'un « ... » la place du complement que le mot regit :
    « de la instanto kande onu agnoskas kom valida ke... » pour quoniam, et de
    meme pour for, jus, kande, kovrar, pasar, proxim. Le rognage ordinaire des
    points la faisait disparaitre, alors qu'elle porte du sens — le livre en
    garde cinquante-cinq autres ailleurs.
    """
    x = re.sub(r'[\s\-\u2013]+$', '', x)
    # Le code de langues se colle parfois a l'ellipse — « ... gradale) de...EFIRS »
    # chez proxim — et la recherche du code en emporte un point. Deux points
    # suffisent donc a la reconnaitre ; on la retablit a trois.
    if re.search(r'\.\.+$', x):
        return re.sub(r'\.\.+$', '...', x)
    # « e c. » abrege « e cetere » : ce point appartient au mot, non a la
    # phrase, et ne doit pas tomber avec la ponctuation finale.
    if re.search(r'(?<![A-Za-zÀ-ÿ])e c\.$', x):
        return x
    x = re.sub(r'[\s\-\u2013.,;:]+$', '', x)
    return x


# Abreviations employees dans le champ du domaine. L'original les pointe
# irregulierement — « (ajuro) » ecrit « bot. », d'autres « bot » tout court.
# On uniformise en les pointant toutes. La liste est EXPLICITE, et non deduite
# d'une regle sur la finale : le meme champ contient des prepositions qui
# finissent aussi par une consonne (« trans., ad », « netrans., pri »), des
# verbes (« qua agas »), des numeraux (« un »), et jusqu'a une formule chimique
# — une regle generale y mettait « C.8 H.8 » et « Natur.-historio ».
MALLONGIGI = set("""
trans netrans netr tran anat anatom arit aritm algeb akust arkeol arkit arkitekt
astr astron biol bot diplomac elektr embriol farmak filoz filozof financ fiz
fizik fiziol fortifik fotogr geogr geol geom gram gramat histol imprim katol kem
kemi kirurg kosmol krist kristan liturg literat magnet mat matem med medic mekan
metaf metapsik meteor meteorol mikrobiol milit mineral mitol muz muzik nav navig
oftalm opt paleogr paleont paleontol pat patol pikt psik retor skerm stat tek
tekn teknol teol teratol versif zool zoolog
""".split())


def pointi(f):
    """Ajoute le point aux abreviations du domaine, et a elles seules."""
    if not f:
        return f
    return re.sub(r'(?<![A-Za-zÀ-ÿ.])([A-Za-zÀ-ÿ]+)(?![A-Za-zÀ-ÿ.-])',
                  lambda m: m.group(1) + '.' if m.group(1).lower() in MALLONGIGI
                  else m.group(1), f)


# Les noms propres qui ouvrent une parenthese dans le livre — pays, personnes,
# divinites, peuples, et les adjectifs de langue et de nation, qui gardent leur
# majuscule en ido. Sans cette liste la regle de minuscule les abimait :
# « (Italia) » devenait « (italia) », « (Voltaire) » « (voltaire) », et
# « (Diana chasera, Tetis, e c.) » chez nimfo perdait sa deesse. La liste a ete
# relevee sur le texte brut, en cherchant toute parenthese ouverte par un mot
# capitalise dont l'edition avait fait une minuscule.
PROPRA = ('Roma', 'Vatikano', 'Afrodito', 'Araba', 'Aug', 'Auguste', 'Azia',
          'Bacchus', 'Britania', 'Cicero', 'Diana', 'Dubois', 'Elizeo', 'Epiro',
          'Francia', 'Greka', 'Grekia', 'India', 'Istanbul', 'Italia', 'Kelti',
          'Latina', 'Louis', 'Mohamedisti', 'Noah', 'Roentgen', 'Suisia',
          'Tartaro', 'Usa', 'Voltaire',
          'Germana', 'Angla', 'Franca', 'Italiana', 'Rusa', 'Hispana', 'Sueda',
          'Skandinava', 'Portugalana', 'Nederlandana', 'Polona', 'Dana',
          'Norvegana', 'Finlandana', 'Cheka', 'Japoniana', 'Sanskrita',
          'Hebrea', 'Turka', 'Chiniana', 'Malaya', 'Slava', 'Hindua')


def minuskligi(f):
    """La majuscule initiale d'un domaine n'a pas lieu d'etre : « (Muziko) »
    s'ecrit « (muziko) ». L'auteur ne s'est pas uniformise. On epargne les noms
    propres et les formules chimiques, reconnues a leur chiffre."""
    if not f or not f[0].isupper():
        return f
    unua = f.split()[0].rstrip('.,)')
    # Un symbole chimique — « M », « M' », « Na » — n'est pas un domaine :
    # « (M : natro, o kalio...) », dans la formule de l'alun, dit ce que la
    # lettre M represente. Un domaine du livre est un mot, non une lettre.
    if len(unua.rstrip("'")) <= 2 and unua.rstrip("'").isupper():
        return f
    if unua in PROPRA or re.search(r'[\d\u2080-\u2089]', unua):
        return f
    return f[0].lower() + f[1:]


# Le meme domaine, ecrit de deux facons par l'auteur — « (anatom.) » une fois
# contre « (anat.) » deux cent vingt-neuf, « (kem.) » deux fois contre
# « (kemio) » cent quatre-vingts. Ce n'est pas une mauvaise lecture : c'est
# l'auteur qui ne s'est pas uniformise, sur quarante ans de fiches. L'edition
# retient LA FORME QU'IL EMPLOIE LE PLUS. Quand les deux sont a moins du double
# l'une de l'autre, c'est l'abregee qui l'emporte : le livre abrege ses domaines
# 2 463 fois contre 746 ou il les ecrit au long, et l'abreviation est donc sa
# maniere. Chaque ligne porte les deux comptes.
#
# Ce qui n'est PAS ici : les formes que rien ne dit equivalentes. « tekn. » et
# « teknol. », « fiz. » et « fiziol. », « paleont. » et « paleogr. », « milit. »
# et « milit-arto », « elektro » et « elektrotekniko » sont des domaines
# distincts, et « (religio kristana) », « (armeo-chefo) » des locutions.
DOMENI_UNIFORMA = {
    'netr.': 'netrans.',            #   3 / 446
    'anatom.': 'anat.',             #   1 / 229
    'zoolog.': 'zool.',             #   1 / 424
    'botaniko': 'bot.',             #   1 / 580
    'pat.': 'patol.',               #   1 / 233
    'kem.': 'kemio',                #   2 / 180
    'tek.': 'tekn.',                #   1 / 117
    'muz.': 'muziko',               #   1 /  84
    'muzik.': 'muziko',             #   1 /  84
    'gramat.': 'gram.',             #   2 /  88
    'geometrio': 'geom.',           #   1 /  83
    'mat.': 'matem.',               #   6 /  61
    'astr.': 'astron.',             #   2 /  27
    'filozof.': 'filoz.',           #   1 /  20
    'filozofio': 'filoz.',          #   1 /  20
    'fiz.': 'fiziko',               #   2 /  37
    'financ.': 'financo',           #   1 /  13
    'mineralogio': 'mineral.',      #   2 /  35
    'mitologio': 'mitol.',          #   2 /  14
    'arkit.': 'arkitekt.',          #   5 /  33
    'arkitekturo': 'arkitekt.',     #   3 /  33
    'algeb.': 'algebro',            #   1 /   9
    'arit.': 'aritm.',              #   2 /   9
    'med.': 'medic.',               #   1 /  32
    'medicino': 'medic.',           #  13 /  32
    'nav.': 'navig.',               #   3 /  38
    'teolo': 'teol.',               #   1 /   6  (« teolo » n'est pas un mot)
    'kristan.': 'kristanismo',      #   1 /   7
    'kristanismo.': 'kristanismo',  #   1 /   7  (le point d'un mot entier)
    'arkeologio': 'arkeol.',        #   1 /   4
    'opt.': 'optiko',               #   2 /   5
    'histologio': 'histol.',        #   7 /   5  — a moins du double : l'abrege
    'kirurgio': 'kirurg.',          #   8 /  13
    'retoriko': 'retor.',           #   7 /   6  — a moins du double : l'abrege
    'mekaniko': 'mekan.',           #   3 /   4
    'meteor.': 'meteorol.',         #   2 /   6
    'paleontol.': 'paleont.',       #   4 /   5
    'paleontologio': 'paleont.',    #   1 /   5
    'elektr.': 'elektro',           #   9 /  20
    'milito': 'milit.',             #   6 /  10
    'imprim.': 'imprim-arto',       #   1 /   3  — le trait d'union, maniere
    'imprimarto': 'imprim-arto',    #   2 /   1    du livre pour ses domaines
    'militarto': 'milit-arto',      #   4 /   8    composes : il l'ecrit ainsi
    'shakoludo': 'shako-ludo',      #   1 /   1    dans TOUS les autres —
    'skermarto': 'skerm-arto',      #   1 /   1    « banko-komerco », « natur-
    'yurocienco': 'yuro-cienco',    #  24 /  15    historio », « politiko-yuro ».
    'akustiko': 'akust.',           #   1 /   1  — egalite : l'abrege
    'diplomaco': 'diplomac.',       #   1 /   1
    'magnetismo': 'magnet.',        #   1 /   1
    'fortifikuro': 'fortifik.',     #   1 /   1
    'teratologio': 'teratol.',      #   1 /   1
    'versifado': 'versif.',         #   1 /   1
    'prosodio': 'prozodio',         #   1 /   1  — « prozodio » est vedette du
                                    #             livre, « prosodio » non
    'teol.katol': 'teol. katol.',   # l'espace perdue entre deux domaines
    'trans.pri': 'trans., pri',
    'meteorologio': 'meteorol.',    #   1 /   6
    'tekniko': 'tekn.',             #   1 / 119
    'maronavigado': 'maro-navig.',  #   1 /   1
}
# Le soulignement releve sur la page porte la forme QUE L'AUTEUR A ECRITE ; le
# champ porte celle que l'edition retient. Pour reconnaitre qu'un souligne est
# le domaine — et ne pas l'envoyer a la liste des filets non places —, il faut
# donc connaitre les deux. Table inverse, pour cet usage seul.
def _plata(x):
    """La chaine reduite a ses lettres : « netrans.,an » et « netrans., an »
    sont le meme domaine, « yuro-cienco » et « yurocienco » aussi."""
    return re.sub(r'[^0-9a-zà-ÿ]', '', x.lower())


DOMENI_VARIANTOJ = {}
for _v, _r in DOMENI_UNIFORMA.items():
    DOMENI_VARIANTOJ.setdefault(_plata(_r), set()).add(_v)
DOMENI_PLATA = {_plata(_v): _r for _v, _r in DOMENI_UNIFORMA.items()}


def alia_formo(u):
    """La forme RETENUE d'un domaine que la page ecrit autrement.

    Le filet de la dactylo couvre « medicino » ; le texte rendu porte
    « medic. ». Cherche tel quel, le filet ne se retrouvait plus, et le domaine
    perdait son italique. Le trait se rompt aussi en fin de ligne, et il ne
    reste qu'un morceau — « cienco » pour « yuro-cienco » : on accepte donc
    aussi le morceau, a partir de quatre lettres.
    """
    p=_plata(u)
    if not p:
        return None
    if p in DOMENI_PLATA:
        return DOMENI_PLATA[p]
    w=uniformigar(u)
    if w != u:
        return w
    if len(p) >= 4:
        for v, r in DOMENI_UNIFORMA.items():
            if p in _plata(v):
                return r
    return None
# On ne remplace que la composante ENTIERE : le champ enumere parfois deux
# domaines — « (arit., algeb.) », « (fiz. e geom.) » —, et chacun compte pour
# une composante. Une composante de plusieurs mots est une phrase de l'auteur,
# non un domaine : « ante la milito universala di 1914-18 », « en la filozofio
# olima », « olima geometrio » gardent leur mot.
RE_KOMPONO = re.compile(r'(\s*,\s*|\s+e\s+)')


def uniformigar(f):
    """Rend au domaine la forme que l'auteur emploie le plus souvent."""
    if not f:
        return f
    out=[]
    for part in f.split(') ('):
        bouts=RE_KOMPONO.split(part)
        for i in range(0, len(bouts), 2):
            b=bouts[i].strip()
            # La forme cherchee l'est a la ponctuation et a la casse pres :
            # « Medicino », « kem » sans son point et « kem. » sont le meme mot.
            r=DOMENI_UNIFORMA.get(b) or DOMENI_PLATA.get(_plata(b))
            if r:
                bouts[i]=bouts[i].replace(b, r)
            # La virgule qui separe deux domaines prend son espace, comme les
            # quatre cents autres : « (netrans.,an) » s'ecrit « (netrans., an) ».
            # Sauf entre deux chiffres : « (en Paris = 1,18 metro) », chez
            # « ulno », porte une decimale et non une enumeration.
            if (i+1 < len(bouts) and not re.search(r'\d', bouts[i])
                    and not re.search(r'\d', bouts[i+2])):
                bouts[i+1]=', ' if ',' in bouts[i+1] else ' e '
        out.append(''.join(bouts))
    return ') ('.join(out)


def pointi_sencoj(t):
    """Meme regle DANS les parentheses d'un sens : tous les qualificatifs ne
    sont pas dans le champ du domaine — « ajuro » porte les siens dans ses deux
    sens, « (arkitekt.) » pointe et « (stofo) » non, ce dernier etant un mot
    entier et non une abreviation."""
    return re.sub(r'\(([^()]{1,120})\)',
                  lambda m: '(' + uniformigar(minuskligi(pointi(m.group(1)).rstrip(' ,')))
                  + ')', t)


def _tondar_fino(s):
    """Le balayage de fin de chaine, qui s'arrete aux points de suspension."""
    m = re.search(r'[\s.\-—–]+$', s)
    if not m:
        return s
    d = list(re.finditer(r'\.{3,}', m.group(0)))
    return s[:m.start() + d[-1].end()] if d else s[:m.start()]


def analizar(e, lexique=None):
    t=e.get('teksto_brut')
    if t is None:
        t=recoller([s for _,s in e['lineoj']], lexique)
    t=re.sub(r'\s+',' ',t).strip()
    for a,b in _texti().items():
        # Idempotence : la couche passe une fois au decoupage et une fois a
        # l'analyse. Quand la cle est un prefixe de son remplacement — ajouter
        # un guillemet fermant, par exemple — la seconde passe l'ajoutait une
        # seconde fois. On s'abstient si le remplacement est deja pose.
        if a in t and b not in t: t=t.replace(a,b)
    # Le fac-simile garde l'espace que la dactylo a laissee autour du tiret
    # d'affixe ; l'edition de lecture recolle. « - as. » est « -as », « - at
    # - . » est « -at- », « bo - . » est « bo- ». Sans quoi la vedette etait
    # vide et l'article introuvable.
    # « -- protestanto. » : le double tiret annonce un article insere apres
    # coup, il n'appartient pas a la vedette. Un tiret SEUL, lui, est l'affixe
    # (« -a », « -oz- ») et reste.
    t=re.sub(r'^[-–]{2,}\s+(?=[A-Za-z+"«])', '', t)
    t=re.sub(r'^([-+])\s+(?=[A-Za-zÀ-ÿ])', r'\1', t)
    t=re.sub(r'^([-+]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]{0,20})\s+-\s*(?=\.)', r'\1-', t)
    t=re.sub(r'^([-+]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]{0,20})\s+-\s*\.', r'\1-.', t)
    # Vedette espacee lettre a lettre — « l a t i r o » pour « latiro » : la
    # dactylo mettait ainsi en valeur, faute d'italique.
    m0=re.match(r'^((?:[A-Za-zÀ-ÿ] ){2,}[A-Za-zÀ-ÿ])(?=\s*\.)', t)
    if m0: t = m0.group(1).replace(' ','') + t[m0.end():]
    # Ligne barree a coups de guillemets et de tirets : la dactylo annulait
    # ainsi une ligne entiere. Ce qui suit le code de langues et ne porte ni
    # lettre ni chiffre ne dit rien — mais laisse la, cette queue empechait le
    # code de s'ancrer en fin de chaine, et « exotera » passait pour
    # « sen-lingua », son DEFIRS reste au milieu de la definition.
    t=re.sub(r'[\s"\u00ab\u00bb\u2019\'.,;:_+*=/|\-\u2013\u2014]{6,}$', '', t)
    # La rature porte parfois des LETTRES — « myelito. ... - DEFIS. vm-----m- ».
    # La regle ci-dessus, qui exige une queue sans lettre ni chiffre, la
    # laissait passer : la definition gardait le barbouillage, et le code, qui
    # ne s'ancrait plus en fin de chaine, etait perdu — l'article passait pour
    # « sen-lingua ». Un jeton qui porte trois tirets de suite n'est aucun mot
    # de la langue ; le livre n'en compte que cinq, tous des ratures.
    t=re.sub(r'[\s.,;:\-\u2013]*\S*-{3,}\S*[\s.,;:\-\u2013]*$', '', t)
    e['teksto']=t
    # Le tapuscrit marque les mots non officiels d'un « + » en exposant ; la
    # tradition ido ecrit une asterisque. On la restitue ici — le fac-simile,
    # lui, garde le signe frappe.
    #
    # PARTOUT, non a la seule vedette : le signe marque aussi la variante qui
    # la suit — « timbro (+tembro) », « tarda (+retarda) » — et les mots cites
    # dans les definitions — « +Seancar », « +Kluzajo », « +Asiejo-mashino ».
    # Deux contextes en sont exclus, ou le « + » est le signe de l'addition et
    # non une marque : « 6 +1, o 4 +3 » chez « sep », et les points d'une
    # figure « AA'+BB'+CC' » chez « involuciono ». On exige donc une LETTRE
    # apres le signe, et rien d'alphanumerique avant lui.
    #
    # Effet de bord voulu : « augmentar » finissait sur « +DEFIS », et son code
    # de langues ne s'ancrait pas — l'article passait pour « sen-lingua ». Avec
    # l'asterisque, que la lecture du code admet deja, il s'ancre.
    t = re.sub(r"(?<![A-Za-zÀ-ÿ0-9'’])\+(?=[A-Za-zÀ-ÿ])", '*', t)
    # La vedette peut etre entre guillemets — « "alpari" », « "amen" » — ou
    # precedee d'un point parasite. On les admet, puis on les retire du mot.
    t = t.lstrip('. ')
    # Emprunt cite : le tapuscrit encadre de guillemets les mots pris tels
    # quels a une autre langue — « amen », « alpari », « angelus », « avoue ».
    # On retient le fait, sans le mettre dans la vedette : la recherche doit
    # continuer de trouver « amen » frappe sans guillemets.
    # Encore faut-il que les guillemets tiennent TOUT le mot. « "brokoli"-kaulo »
    # n'est pas un emprunt cite : c'est un mot ido dont le premier element seul
    # est emprunte, et les editions, qui encadrent de chevrons la vedette citee,
    # en mettaient une seconde paire autour de la premiere. On refuse donc la
    # fermante suivie d'une minuscule ou d'un tiret — le mot continue. Suivie
    # d'une capitale, elle ouvre la definition : « "madras"Kapovesto », ou
    # l'espace a manque a la frappe.
    e['citita'] = bool(re.match(r'^["\u00ab\u201c][^"\u00bb\u201d]{1,60}'
                                r'["\u00bb\u201d](?![a-zà-ÿ-])', t))
    # Les lettres accentuees appartiennent au mot : sans elles « ampere » se
    # coupait en « amp » et le reste tombait dans la definition.
    # Locution latine ou anglaise prise pour vedette : le tapuscrit l'encadre de
    # guillemets — « "a posteriori" », « "high life" ». Le mot-vedette est alors
    # la locution ENTIERE ; sans cette regle « a posteriori » se reduisait a
    # « a » et sa definition commencait par « posteriori" ».
    mq=re.match(r'^["\u201c]?([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]*'
                r'(?: [A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\'’-]*){0,2})["\u201d]'
                r'\s*(?:\.|(?=\s*[A-ZÀ-Ý(]))', t)
    if mq:
        e['vedetto']=mq.group(1); m=None; resto=t[mq.end():].strip()
    else:
        m=re.match(r'^(\+?-?["\u201c]?[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ"’\'\u201d-]*)\s*\.?', t)
        e['vedetto']= (m.group(1).strip('.').strip('"\u201c\u201d')
                       .replace('+','*',1)) if m else ""
        resto = t[m.end():].strip() if m else t
    # Le bruit qui suit parfois le code — « - DEFIRS. --- » — empechait
    # l'ancrage en fin de chaine, et l'entree passait pour « sen-lingua ».
    # Les POINTS DE SUSPENSION, eux, appartiennent au texte : ils tiennent la
    # place du complement, et huit articles finissent dessus — « Kambie di... »
    # chez « po », « Qua havas tri... » chez « tri- », « Profite da... Destine
    # di... » chez « por ». Le balayage les emportait, sauf quand un guillemet
    # fermant les protegeait (« qua tendencas a... »). On garde donc le dernier
    # groupe de points du balayage et on ne retire que ce qui le suit.
    resto = _tondar_fino(resto)
    e['lingui']=[]; e['kodo']=None
    me = RE_EPELE.search(resto)
    if me:
        noms=[EPELE.get(x.strip(' .')) for x in me.group(1).split(',')]
        if all(noms):
            e['lingui']=noms; e['kodo']=me.group(1).strip()
            resto = _kupar(resto[:me.start()])
    # Le code n'est pas toujours precede d'un tiret. Il se colle au point
    # (« agar lo.DEFIS. »), a la parenthese fermante (« (anke metaf.)DEFIRS »),
    # mais aussi a une parenthese OUVRANTE restee ouverte (« ...alambiko.
    # (DEFIRS »), a une virgule (« ...deliberita, DEFIS ») ou a rien du tout
    # (« ...kavalrio DEFIRS »). Vingt-et-un articles gardaient ainsi leur code
    # au milieu de la definition et passaient pour « sen-lingua ». La casse
    # protege : _lire_code exige un jeton majoritairement haut de casse, et le
    # dernier mot d'une definition ne l'est jamais.
    # L'auteur ajoute parfois une remarque APRES le code : « ... - DEFIS. (Ta
    # vorto ne esas sinonimo di mariajar... ) ». Le code n'etant plus en fin de
    # chaine, il n'etait pas lu, et l'article passait pour « sen-lingua ». On
    # met donc la remarque de cote le temps de lire le code, puis on la remet.
    remarko = ''
    if not e['kodo']:
        mr = re.match(r'^(.*?[-–]\s*[A-Za-z]{1,12}\s*\.)\s*(\(.{6,}\))\s*$',
                      resto, re.S)
        if mr and _lire_code(re.search(r'([A-Za-z]{1,12})\s*\.$', mr.group(1)).group(1)):
            # Le point final doit tomber : la recherche du code exige des
            # lettres en toute fin de chaine.
            resto, remarko = mr.group(1).rstrip(' .'), mr.group(2)
    mj = None if e['kodo'] else re.search(r'(?:[-–.,()*]|\s|^)\s*([A-Za-z]{1,12})$', resto)
    if mj:
        li=_lire_code(mj.group(1))
        if li:
            e['lingui']=li; e['kodo']=mj.group(1)
            resto = _kupar(resto[:mj.start()])
    if remarko:
        resto = (resto.rstrip(' -–.') + '. ' + remarko) if resto else remarko
    # Le code de langues qui n'est PAS au bout. L'auteur l'a parfois pose apres
    # un premier sens et a continue — « cilio. (anat.) Pilo... - F. (bot.) Sorto
    # di pilo... - F. » —, ou la frappe a laisse une scorie derriere lui :
    # « - DE. s q c i » chez hidranto, « - DEFIS. pre- » chez studiar. Le code
    # restait alors AU MILIEU de la definition, ou il n'a rien a faire, et
    # l'article passait pour « sen-lingua ».
    #
    # On ne touche qu'a deux cas surs : l'article n'a pas de code, ou il porte
    # deja le MEME. Un code different au milieu du texte est autre chose — chez
    # « staciono », « (autofiakri - F. taxi - autobusi, e c.) » donne le mot
    # francais, il ne clot pas l'article.
    #
    # Quand ce qui suit ouvre un sens — un domaine entre parentheses, ou un
    # tiret suivi d'une capitale —, la coupure se fait la : le code marquait la
    # fin d'un sens. On la note d'un signe que le decoupage lira.
    mi = re.search(r'\s*[-–]\s*([A-Z][A-Zl]{0,11})\.?\s+(?=\S)', resto)
    li = _lire_code(mi.group(1)) if mi and mi.group(1) != 'L' else None
    if li and (not e['kodo'] or e['kodo'].upper() == mi.group(1).upper()):
        if not e['kodo']:
            e['lingui']=li; e['kodo']=mi.group(1)
        gauche = resto[:mi.start()]; droite = resto[mi.end():].lstrip()
        mq = re.match(r'\(([a-zà-ÿ]{2,12})\.?\)', droite)
        if (mq and mq.group(1) in MALLONGIGI) or re.match(r'[-–]\s*[A-ZÀ-Ý]', droite):
            resto = gauche.rstrip(' -–.,;:') + KUPO + droite
        elif re.search(r'[.!?)]\s*$', gauche):
            resto = gauche.rstrip(' -–.,;:') + '. ' + droite
        else:
            resto = gauche.rstrip() + ' ' + droite
    # Le numero de sens qui pend au bout de l'article, sans rien apres lui :
    # « forsan. Adverbo qua signifikas "..." - II. » — la dactylo a annonce un
    # second sens qu'elle n'a pas frappe. Seul, le numero ne dit rien, et
    # l'edition ecarte deja ses pareils au milieu du texte. On exige le tiret
    # qui l'annonce, pour ne pas rogner « la rejo Francisko I ».
    resto = re.sub(r'[.;,]?\s*[-–]\s*(?:I{1,3}|IV|VI{0,3}|IX|X)\.?$', '', resto)
    resto = resto.lstrip(' -–.,;:')
    # « ed. (Videz "e"). » : la parenthese porte un RENVOI, pas un domaine. Prise
    # pour un domaine, elle laissait l'article sans definition du tout.
    mf=None if re.match(r'^\(\s*(?:Videz|videz|Vid\.)\b', resto) else (
        RE_FAKO.match(resto) or RE_FAKO2.match(resto))
    # Le domaine porte souvent une ponctuation parasite, heritee de la frappe :
    # « zool, », « .trans », « patol, ». Et il peut contenir une date, dont les
    # chiffres sont a redresser comme ailleurs — « olim, ante l9l5 ».
    e['fako']= uniformigar(minuskligi(pointi(cifri(mf.group(1).strip(' .,;:'))))) if mf else None
    if e['fako']: e['fako']=formuli(e['fako'])
    if mf: resto = resto[mf.end():]
    # Deux parentheses de suite : la seconde precise la premiere et non le
    # sens. « pensar. (trans. e netrans.) (ulo, ad ulo, pri ulu od ulo) » —
    # le regime appartient au marqueur de transitivite, pas a la definition,
    # qui commencait donc par une parenthese orpheline.
    if e['fako']:
        m2 = re.match(r'^[\s.,;:\u2013-]*\(([^()]{1,40})\)\s*\.?\s*(?=[-\u2013]?\s*(?:[IVX]{1,4}\.|[A-Z\u00c0-\u00dd]))', resto)
        if m2:
            # La seconde parenthese est un renseignement de meme nature que la
            # premiere, et lui revient le meme traitement : minuscule initiale,
            # chiffres redresses, POINT rendu a l'abreviation. Recollee telle
            # quelle, elle ressortait nue quand ses voisines etaient pointees —
            # « (trans.) (tekn) », « (netrans.) (patol) », « (netrans.) (Kemio) ».
            dua = uniformigar(minuskligi(pointi(cifri(m2.group(1).strip(' .,;:')))))
            e['fako'] = "%s) (%s" % (e['fako'], dua)
            resto = resto[m2.end():]
    resto = resto.lstrip(' -–.,;:')
    # Elision : « ka(d) », « on(u) », « a(d) ». La lettre entre parentheses
    # appartient au mot — elle ne s'ajoute que devant une voyelle. Elle etait
    # lue comme un domaine, et s'affichait separee de la vedette, dans une
    # autre couleur.
    #
    # Ce n'en est une que si la vedette est breve ET la parenthese d'UNE
    # lettre. Sans cette double condition on happerait « afina (ad) »,
    # « plena (de) », ou la parenthese porte une preposition regie et non une
    # lettre elidee.
    # Interjection : le point d'exclamation appartient au mot, non a la
    # definition. « he » se lit « he! », et sa definition commence apres.
    if resto.startswith('!') and e['vedetto'] and len(e['vedetto'].lstrip('*')) <= 6:
        e['vedetto'] = e['vedetto'] + '!'
        resto = resto[1:].lstrip(' -–.,;:')
    if (e['fako'] and len(e['fako'])==1 and e['fako'].isalpha()
            and e['vedetto'] and len(e['vedetto'].lstrip('*')) <= 3):
        e['vedetto'] = "%s(%s)" % (e['vedetto'], e['fako'])
        e['fako'] = None
    e['latina']= [x.strip(' .') for x in RE_LATINA.findall(resto)]
    resto = RE_LATINA.sub('', resto).strip(' -–')
    # Un nom releve a l'oeil l'emporte : la machine ne peut pas savoir que
    # « capparia spi nosa » est « capparia spinosa », aucun des deux morceaux
    # n'etant un mot latin.
    _man = latinaji_manuala().get("%s@%d:%d" % (e.get('vedetto'), e.get('image', -1),
                                                e.get('ligno', -1)))
    if _man:
        e['latina'] = [x.strip() for x in _man.split(';') if x.strip()]
    e['simbolo']= None
    # Un NUMERO de sens entre parentheses n'est pas un domaine : « romano. (I)
    # Verko literaturala... », « vice. (l) qua pre-nominesis... » — le « l »
    # etant le 1 de la dactylo. Les editions renumerotent les sens elles-memes ;
    # garde comme domaine, le numero s'affichait a la place du domaine.
    if e['fako'] and re.fullmatch(r'(?:[IVX]{1,4}|[a-z]|[0-9]|l)', e['fako'].strip()):
        e['fako'] = None
    # Le numero peut PRECEDER un vrai domaine : « ramo. (l) (bot.) Mikra
    # brancho... ». La fusion des deux parentheses gardait alors les deux, et
    # l'article s'annoncait « (1) (bot.) ». On ne jette que le numero.
    if e['fako']:
        m1 = re.fullmatch(r'(?:[IVX]{1,4}|[a-z]|[0-9]|l)\)\s*\((.+)', e['fako'].strip())
        if m1: e['fako'] = m1.group(1)
    # Une FORMULE chimique posee juste apres la vedette — « asparagino. (C8 H8
    # AZ2 O6). Substanco... » — n'est pas un domaine non plus : c'est le meme
    # renseignement que « Simbolo kemiala : ... » ailleurs dans le livre, et il
    # va au meme champ, pour se rendre de la meme facon.
    if (e['fako'] and e['simbolo'] is None
            and re.fullmatch(r"[A-Z][A-Za-z0-9\u2080-\u2089\s.'()/-]*", e['fako'].strip())
            and re.search(r'[0-9\u2080-\u2089]', e['fako'])):
        e['simbolo'] = e['fako'].strip()
        e['fako'] = None
    senci=[_kupar(x.lstrip(' -–.,;:')) for m in resto.split(KUPO)
           for x in RE_SENCO.split(m) if x.strip(' -–.,;:')]
    e['senci']= senci if senci else ([resto] if resto else [])
    # La numerotation entre parentheses dont le « (1) » est parti au domaine :
    # on coupe a la place des numeros restes (voir RE_ORFA_NUM).
    S=[]
    for s in e['senci']:
        if RE_ORFA_NUM.search(s) and not RE_NUM_UNESMA.search(s):
            S.extend(x for x in (_kupar(y.lstrip(' -–.,;:'))
                                 for y in RE_ORFA_NUM.split(s)) if x)
        else:
            S.append(s)
    e['senci']=S
    # Rattrapage : le code peut rester au bout du DERNIER sens quand une note
    # le suivait dans l'original et que le decoupage en sens l'a isole. On le
    # releve la aussi — et s'il double celui deja lu, on le retire du texte.
    if e['senci']:
        mk = re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][-1])
        if mk:
            li=_lire_code(mk.group(1))
            if li:
                if not e['kodo']: e['lingui']=li; e['kodo']=mk.group(1)
                q=e['senci'][-1][:mk.start()].rstrip(' -–.,;:')
                if q: e['senci'][-1]=q
                else: e['senci'].pop()
    if e['image'] in PAGINI_NEOFICALA and e['vedetto'] and not e['vedetto'].startswith('*'):
        e['vedetto'] = '*' + e['vedetto']
    v=e['vedetto']
    e['drapeli']=list(e.get('drapeli_pre',[]))
    if not v: e['drapeli'].append('sen-chefvorto')
    elif not _finalo_ok(e): e['drapeli'].append('finalo-nekustumala')
    if not e['kodo']: e['drapeli'].append('sen-lingua')
    # Le drapeau « korektigita » disait « au moins une cellule corrigee
    # automatiquement » — une information de provenance, non un doute. Toutes
    # les definitions ayant ete relues une a une, il ne designait plus de
    # travail restant : il est retire. Le compte reste dans e['korektita'],
    # pour qui veut mesurer.

    if e['image'] in (546,547): e['drapeli'].append('pagino-nefidinda')
    return e

# Les deux dernieres pages du livre portent une liste a part, annoncee par son
# propre titre : « LISTO de vorti qui, pro lia teknikaleso e probiteso multa-
# yara, probable adoptesos da la Akademio di Ido ». Ce sont donc, par
# definition, des mots non encore officiels — l'asterisque leur revient, mais
# la dactylo ne l'a pas frappee, le titre valant pour toute la liste.
PAGINI_NEOFICALA = (637, 638)

def _klavo_ordino(v):
    """La vedette telle qu'elle se RANGE, sa marque de tete otee.

    L'asterisque du mot non officiel et le tiret de l'affixe ne sont pas des
    lettres, et le livre ne les range pas : « -acho » est entre « acetono » et
    « aciano », « -eyo » entre « exutorio » et « ez ». Compares tels quels, ils
    passaient avant toute lettre — chacun des 126 affixes et mots non officiels
    rompait donc l'ordre par sa seule marque, et entrainait son voisin avec
    lui. Quatre-vingt-cinq drapeaux ne disaient que cela.

    Le point d'exclamation de l'interjection ne se range pas davantage :
    « ah! » se cherche a « ah ». Ni le tiret FINAL du suffixe — « -an- » se
    range avec « an » —, ni l'espace de la locution latine : le livre pose
    « a posteriori » entre « apostata » et « apostemo », donc a « aposteriori ».
    """
    # L'accent ne se range pas non plus : « ampèremetro » precede « ampla »
    # dans le livre, ce que seul un « e » sans accent explique. Le tapuscrit
    # n'en porte que sur des noms empruntes — ampère, Roentgen.
    v = unicodedata.normalize('NFD', v.lower())
    v = ''.join(c for c in v if not unicodedata.combining(c))
    # Les guillemets ne se rangent pas davantage, ou qu'ils soient : le livre
    # range « "brokoli"-kaulo » a « brokoli-kaulo ». L'espace insecable qui les
    # accompagne dans l'edition part avec eux.
    v = v.lstrip('*+"«.-').rstrip('!').rstrip('-')
    return re.sub('[\\s\u00a0"«»\u201c\u201d]', '', v)


# La DESINENCE ne compte pas dans le rangement du livre. C'est une regle qu'il
# n'enonce pas, mais qu'il suit : « aktinio » precede « aktinika » parce que
# l'auteur range « aktini » avant « aktinik », le -o et le -a n'y entrant pas.
# Comparees mot entier, ces deux vedettes passaient pour un desordre, et neuf
# cents autres avec elles.
#
# L'auteur ne s'y tient pas toujours : il ecrit « astrakano » puis « astro »,
# ou la racine seule voudrait l'inverse — « astr » avant « astrakan ». Les deux
# lectures sont donc gardees, et le drapeau ne se leve que si TOUTES DEUX sont
# rompues : ce qu'aucune des deux conventions n'explique.
FINALES_ORDINO = ('ar', 'ir', 'or', 'o', 'a', 'e', 'i')


def _klavo_radiko(v):
    """La vedette rangee, sa desinence otee en plus."""
    k = _klavo_ordino(v)
    for d in FINALES_ORDINO:
        if k.endswith(d):
            return k[:-len(d)]
    return k


# Le suffixe ne compte pas plus que la desinence, et pour la meme raison : le
# rangement suit la RACINE. « venerala » precede « veneracar » parce que le
# premier est vener-al-a et le second venerac-ar ; « inventariar » precede
# « inventar » parce que les deux sortent de invent-. C'est ainsi que plusieurs
# dictionnaires de l'ido les analysent, et le livre les range de meme.
#
# Le depouillement s'arrete a UN suffixe, et ne descend jamais sous cinq
# lettres : sans cette borne « metalo » deviendrait « met- » et « histerio »
# « hist- ». Cette troisieme lecture ne peut qu'OTER des drapeaux — il en faut
# trois pour en poser un —, jamais en ajouter.
SUFIXI = tuple(sorted(
    ('ari', 'atr', 'ebl', 'end', 'eri', 'esk', 'estr', 'ier', 'ind', 'ism',
     'ist', 'oid', 'ach', 'ad', 'aj', 'al', 'an', 'ar', 'ed', 'eg', 'em',
     'er', 'es', 'et', 'ey', 'id', 'if', 'ig', 'ik', 'il', 'in', 'iv', 'iz',
     'oz', 'ul', 'um', 'ur', 'uy'), key=len, reverse=True))


def _klavo_radikalo(v, mini=5):
    """La vedette rangee, sa desinence et UN suffixe otes."""
    r = _klavo_radiko(v)
    for x in SUFIXI:
        if r.endswith(x) and len(r) - len(x) >= mini:
            return r[:-len(x)]
    return r


# Le livre se termine par deux listes a part, qui recommencent chacune
# l'alphabet : un addendum de cinq articles (image 636) et la « LISTO de vorti
# qui... probable adoptesos da la Akademio di Ido » (images 637-638). Leur
# premiere vedette recule forcement dans l'alphabet ; ce n'est pas un desordre.
KOMENCO_DE_SEKCIONO = (636, 637)


# La nature grammaticale, telle que le livre l'annonce lui-meme en tete de
# definition : « Prepoziciono qua indikas... », « Interjeciono qua expresas... »
RE_GRAMATIKA = re.compile(
    r'^\(?\s*(?:prepoziciono|konjunciono|pronomo|adverbo|interjeciono'
    r'|sufixo|prefixo|artiklo|partikulo|des?inenco)', re.I)


def _finalo_ok(e):
    """La finale de la vedette est-elle celle d'un mot ido ?

    La question n'a de sens que pour un MOT DE LA LANGUE. Trois familles y
    echappent, et les signaler etait une erreur de categorie :

      * l'AFFIXE — « -eyo », « poli- », « bo- » —, dont le tiret dit
        precisement qu'il n'est pas un mot. 78 cas ;
      * le mot que le livre declare lui-meme GRAMMATICAL : « an.
        Prepoziciono qua indikas relato di kontigueso », « fi! Interjeciono
        qua expresas la desprizo di ulo ». L'ido ne donne pas de finale en
        -o/-a/-e/-i a ses prepositions, pronoms et interjections. 51 cas ;
      * l'EMPRUNT CITE — « amen », « angelus », « cambium » —, que l'auteur
        entoure de guillemets parce qu'il n'est pas ido. 50 cas.

    Ce qui reste — les numeraux « cent », « dek », les noms de notes « b »,
    « c », « d », et les prepositions que le livre ne qualifie pas — est
    legitime aussi, mais rien dans le texte ne permet de le dire.
    """
    v = e.get('vedetto') or ''
    if not v: return True
    if v.startswith('-') or v.rstrip('!').endswith('-'): return True
    if e.get('citita'): return True
    S = e.get('senci') or []
    if S and RE_GRAMATIKA.match(S[0].lstrip('( ')): return True
    return any(v.lower().endswith(f) for f in FINALES_OK)


# L'ordre des lettres du code est celui du livre : D E F I R S, puis L — le
# latin, que quatre-vingt-douze codes mettent en dernier —, puis les langues
# rares. Vingt-deux codes le rompent : « DEFSR » chez alibio, « ED » chez
# sendar, « FISDE » chez grano, « dEFIRS » ou « DEFlS » ou la capitale et le I
# ont ete abimes a la lecture. Rien ne s'y repete — c'est l'ordre seul qui
# differe —, et l'edition le remet, la ligne brute gardant la graphie de la
# page. Les notations qui EPELLENT la langue en sont exemptes : « FDSued »,
# « DERPol », « Gr », « Ned » ne sont pas des suites de lettres.
ORDINO_KODO = 'DEFIRSLPGN'


def ordinigi_kodojn(ent):
    """Remet les lettres du code dans l'ordre du livre. Rend le nombre pose."""
    n = 0
    for e in ent:
        k = e.get('kodo')
        if not k or not k.isalpha(): continue
        if k in ABREV or k in EPELE or any(k.endswith(a) for a in ABREV): continue
        L = ['I' if c == 'l' else c.upper() for c in k]
        if not all(c in ORDINO_KODO for c in L): continue
        neu = ''.join(sorted(L, key=ORDINO_KODO.index))
        if neu != k:
            e['kodo'] = neu
            e['lingui'] = [LANGUI[c] for c in neu]
            n += 1
    return n


def drapeli_ordino(ent):
    """Pose le drapeau d'ordre sur toute la liste, et rend le nombre pose.

    Le drapeau se lit sur la SUITE des vedettes : il se repose donc en entier
    des qu'une vedette change, ou qu'un article s'ajoute. Une vedette rompt
    l'ordre quand elle recule sur les TROIS lectures — mot entier, racine, et
    racine depouillee de son suffixe (voir _klavo_radiko et _klavo_radikalo) —,
    et qu'elle n'ouvre pas une des listes finales.
    """
    for e in ent:
        if 'ordino-ruptita' in (e.get('drapeli') or []):
            e['drapeli'].remove('ordino-ruptita')
    v=[_klavo_ordino(e.get('vedetto') or '') for e in ent]
    r=[_klavo_radiko(e.get('vedetto') or '') for e in ent]
    d=[_klavo_radikalo(e.get('vedetto') or '') for e in ent]
    unua={}
    for e in ent: unua.setdefault(e.get('image'), id(e))
    n=0
    for i in range(1, len(v)):
        if not (v[i] and v[i-1] and r[i] and r[i-1] and d[i] and d[i-1]): continue
        if v[i] >= v[i-1] or r[i] >= r[i-1] or d[i] >= d[i-1]: continue
        if (ent[i].get('image') in KOMENCO_DE_SEKCIONO
                and unua.get(ent[i].get('image')) == id(ent[i])): continue
        # Les quatre locutions latines — « a posteriori », « ex libris » — sont
        # rangees tantot comme un seul mot, « aposteriori » entre « apostata »
        # et « apostemo », tantot comme deux, « ex libris » avant « exajerar ».
        # Le livre ne dit pas laquelle des deux ; on ne les compte donc pas.
        if ' ' in (ent[i].get('vedetto') or '') or ' ' in (ent[i-1].get('vedetto') or ''):
            continue
        ent[i].setdefault('drapeli', []).append('ordino-ruptita'); n+=1
    return n


def e_ok(e):
    v=e.get('vedetto') or ""
    # Une vedette d'une seule lettre est legitime : « a », « b », « c »... sont
    # les notes de la gamme. Seule la vedette VIDE n'est pas un article.
    if not v: return False
    # « p. 83, an-pos "cetato" : » n'est pas un article mais un renvoi de
    # l'errata, qui dit ou inserer l'article suivant.
    if re.match(r'^p\.\s*\d', e.get('teksto') or ''): return False
    # Le folio courant, lu comme du texte : « 110 » se decode « llO », « 111 »
    # « lll ». Un tel jeton, sans definition, n'est pas un mot.
    if not (e.get('senci') or []) and re.fullmatch(r'[lI1O0]{2,4}', v): return False
    return True

# La locution se presente toujours de la meme maniere : un groupe qui commence
# par une capitale et que suit un deux-points. Le soulignement de l'auteur la
# confirme ; la forme la trouve, meme la ou la relecture a corrige une coquille
# et ou la chaine relevee sur la grille ne se retrouve plus telle quelle.
# La VIRGULE fait partie de la locution : l'auteur empile parfois des locutions
# paralleles qui partagent une definition — « Extraktar radiko, quadrata,
# kubala, di nombro : ... », c'est-a-dire la racine carree et la racine cubique
# en une seule fois ; « La matematiki pura, la mekaniko pura : ... ». Sans elle,
# la definition qui suit grossissait le corps de la locution PRECEDENTE, qui
# n'en pouvait mais.
RE_LOKUCO=re.compile(r'(?:^|(?<=[.;:]\s)|(?<=\)\s)|(?<=[-\u2013]\s))'
                     r'([A-ZÀ-Ý][A-Za-zà-ÿ]+(?:[-, ]+[A-Za-zà-ÿ]+){0,6})\s*:\s')
# Un qualificatif de tete : « (matem.) », « (kemio) ». Une lettre ou un chiffre
# seul entre parentheses est un numero d'enumeration, non un domaine.
RE_KVAL=re.compile(r'(?:[-\u2013\s]*\((?![A-Za-z0-9]\))[^()]{1,60}\)\s*)+$')
RE_NUMERO=re.compile(r'\(([A-Za-z0-9])\)\s*$')
# Le meme qualificatif, mais en TETE : « *botono. (elektr.) Mikra cilindro... »
# porte son domaine apres la vedette, non avant elle comme « (geom.) arko
# inflexita : ... ». Il va au champ `fako` dans les deux cas.
RE_KVAL_KAPO=re.compile(r'^(?:\((?![A-Za-z0-9]\))[^()]{1,60}\)\s*)+')
# La locution ouvre parfois une PARENTHESE : « estado. Eso mentala... (estado
# civila : la situeso di persono kom filio legitima o ne-legitima...) ». C'est
# la meme chose qu'ailleurs — soulignee, suivie du deux-points, portant sa
# propre definition —, et la parenthese ne la degrade pas : « estado civila » se
# cherche comme « estado ». Elle s'y ecrit souvent en minuscule, la parenthese
# tenant lieu d'ouverture ; on n'exige donc pas la capitale ici.
# Un ARTICLE ENTIER glisse entre parentheses dans la definition d'un autre :
# « butono. ... (*botono. (elektr.) Mikra cilindro, ek materio elektro-ne-
# konduktiva...) ». Ce n'est pas une locution mais un mot a part, avec son
# domaine et sa definition — et l'asterisque, dont l'auteur marque le mot non
# encore officiel, le distingue de l'abreviation de domaine qui a la meme
# forme : « (trans. ... », « (anat. ... », « (metaf. ... ». Le livre n'en
# compte qu'un ; sans lui, « botono » ne se cherchait pas.
RE_SUBARTIKLO=re.compile(r'\(\s*(\*[A-Za-zÀ-Ý][A-Za-zà-ÿ-]{2,})\s*\.\s*')
RE_LOKUCO_KRAMPA=re.compile(r'\(\s*([A-Za-z\u00c0-\u00ff][A-Za-z\u00e0-\u00ff]*'
                            r'(?:[- ][A-Za-z\u00e0-\u00ff]+){0,4})\s*:\s')
# Les desinences grammaticales de l'Ido : participes, verbe, substantif,
# adjectif, adverbe, pluriel. On les ote pour comparer deux mots par leur
# RACINE — « inflexar » et « arko inflexita » n'ont pas la meme fin, mais le
# meme mot. De la PLUS LONGUE a la plus courte : « inflexita » doit rendre
# « inflex », non « inflexit », faute de quoi le verbe ne s'y reconnait pas.
FINAJI=('anta','inta','onta','ata','ita','ota',
        'ar','as','is','os','us','o','a','e','i')


def _radiko(m):
    """La racine du mot, sa desinence otee.

    On n'ote rien qui laisserait moins de quatre lettres : sur un radical si
    court, deux mots sans rapport se ressemblent trop — « bear » n'est pas
    « be- », et « arko » n'est pas « ark- ».
    """
    m=m.lower().strip(' .,;:\u00ab\u00bb"\'')
    for d in FINAJI:
        if m.endswith(d) and len(m) - len(d) >= 4:
            return m[:-len(d)]
    return m


def _citas_vedeton(loko, vedetto):
    """La locution reprend-elle le mot de l'article ?

    Dans une parenthese, le deux-points introduit aussi la GLOSE, qui n'est pas
    une locution : « (antonimo : inflaco) », « (analogie : sur la kapo di ula
    repteri) », « (simbolo kemiala : Ir) ». L'auteur les souligne comme les
    locutions — le soulignement ne les separe donc pas. Ce qui les separe, c'est
    que la locution CITE le mot de l'article, sous une forme ou une autre :
    « estado civila » sous « estado », « arko inflexita » sous « inflexar »,
    « relate » sous « relatar ». La glose, elle, parle d'autre chose.

    Hors parenthese, la capitale distinguait les deux ; entre parentheses la
    locution perd sa capitale, et cette citation en tient lieu.
    """
    r=_radiko(vedetto)
    if len(r) < 4: return False
    # On compare par le DEBUT : « konstanta » rend « konst » — la desinence
    # -anta y passe pour un participe qu'elle n'est pas — la ou « konstanto »
    # rend « konstant ». Exiger l'egalite separait les deux ; le prefixe les
    # reunit, sans rapprocher pour autant « nun » de « moloso ».
    for w in loko.split():
        u=_radiko(w)
        if len(u) < 4: continue
        if u == r or u.startswith(r) or r.startswith(u): return True
    return False


def _fermo(t, i):
    """L'index de la parenthese qui ferme celle ouverte en `i`, ou None.

    Le tapuscrit ne ferme pas toujours : « inflexar » ouvre une parenthese que
    la ligne suivante, tronquee, n'a jamais close. Compter les niveaux le dit
    sans se tromper, et ne prend pas la fermeture d'une parenthese INTERIEURE —
    « ... tangenta per olia somiti (quale la embracilo tipografiala) » — pour
    celle de la locution.
    """
    n=0
    for j in range(i, len(t)):
        if t[j] == '(': n += 1
        elif t[j] == ')':
            n -= 1
            if n == 0: return j
    return None


def _enhavas(tuto, parto):
    """`parto` est-il un morceau de `tuto`, aux mots entiers ?

    La comparaison se fait mot a mot, ponctuation otee : le filet releve
    « quadrata » la ou la locution ecrit « quadrata, ».
    """
    def _mots(s): return [w.strip('.,;:') for w in s.lower().split() if w.strip('.,;:')]
    A, B = _mots(tuto), _mots(parto)
    if not A or not B or len(B) > len(A): return False
    return any(A[i:i+len(B)] == B for i in range(len(A)-len(B)+1))


def _kongruas(a, b):
    """Deux chaines designent-elles la meme locution ?"""
    a=a.lower().strip(' .:'); b=b.lower().strip(' .:')
    if a == b: return True
    # Mot a mot, la ponctuation de fin otee : le filet de « radiko » s'arrete
    # sur « Extraktar radiko, quadrata » quand la locution ecrit « quadrata, ».
    # Sans cela la virgule, presente d'un cote et pas de l'autre, faisait
    # echouer la comparaison des debuts.
    pa=[w.strip('.,;:') for w in a.split()]
    pb=[w.strip('.,;:') for w in b.split()]
    if not pa or not pb: return False
    # Le premier mot suffit s'il est long : « Prpporciono » relu
    # « Proporciono » reste reconnaissable, et la suite est identique.
    import difflib
    if len(pa) == len(pb):
        return difflib.SequenceMatcher(None, a, b).ratio() >= 0.85
    # Le filet s'arrete parfois avant la fin de la locution — « Elektro » pour
    # « Elektro pozitiva ». Un debut assez long vaut identification.
    court, long = (pa, pb) if len(pa) < len(pb) else (pb, pa)
    if long[:len(court)] == court and len(" ".join(court)) >= 5: return True
    return False


KOMENCO="\ue000"; FINO="\ue001"     # bornes de l'italique, invisibles au texte


def marki(t, motifs, pozitaj=()):
    """Encadre de bornes chaque passage a mettre en italique.

    On pose les plus longs d'abord : « (aludante persono) » contient
    « persono », et l'ordre inverse aurait coupe la parenthese en deux.
    """
    if not t or not (motifs or pozitaj): return t
    spans=[]
    # Les italiques posees a l'oeil : le contexte donne la place, les accolades
    # disent ce qui la prend. Elles passent AVANT les filets, qui ne doivent pas
    # recouper un passage deja borne.
    for kun, sp in pozitaj:
        i=t.find(kun)
        if i < 0: continue
        for a,b in sp: spans.append((i+a, i+b))
    for u in sorted(motifs, key=len, reverse=True):
        for m in _tuti(u, t):
            if any(not (m.end() <= a or m.start() >= b) for a,b in spans): continue
            spans.append((m.start(), m.end()))
    if not spans: return t
    out=[]; prec=0
    for a,b in sorted(spans):
        out.append(t[prec:a]); out.append(KOMENCO+t[a:b]+FINO); prec=b
    out.append(t[prec:])
    return "".join(out)


def _tuti(u, t):
    if not u.strip(): return []
    mo=re.compile(r'(?<![A-Za-z\u00c0-\u00ff])'
                  + r'\s+\*?'.join(re.escape(w) for w in u.split())
                  + r'(?![A-Za-z\u00c0-\u00ff])', re.I)
    return list(mo.finditer(t))


# Une locution qui est un NOM PROPRE garde sa capitale. Le livre n'en compte
# qu'une : le Grand Orient de la franc-maconnerie.
LOKUCI_PROPRA = ('Granda Oriento',)


def minuskla_lokuco(l):
    """La locution s'ecrit comme une vedette : en minuscule."""
    if not l or l in LOKUCI_PROPRA or not l[0].isupper(): return l
    return l[0].lower() + l[1:]


def majuskla_komenco(t):
    """Initiale capitale, comme les dix mille autres definitions du livre.

    On ne touche qu'a une definition qui COMMENCE par une lettre minuscule :
    celle qui s'ouvre sur une parenthese — « (bot.) ... » — porte un domaine,
    et le domaine s'ecrit en minuscule. Un renvoi d'un seul mot tres court —
    « ica : ca » — n'est pas une phrase et garde le sien.
    """
    if not t: return t
    i=0
    while i < len(t) and t[i] in ' \ue000\ue001': i += 1
    if i >= len(t) or not t[i].isalpha() or not t[i].islower(): return t
    u=t.strip()
    if len(u) <= 3 and ' ' not in u: return t
    return t[:i] + t[i].upper() + t[i+1:]


# --- Le symbole chimique ----------------------------------------------------
#
# Le livre l'ecrit de dix facons : « . – Simbolo kemiala : Al », « . Simbolo
# kemiala : Al » sans tiret, « . – Simbolo kem. Rh » abrege et sans deux-points,
# en minuscule, ou en incise entre parentheses. Pire que l'inegalite : la ou
# l'auteur a souligne l'etiquette, « Simbolo kemiala : » a exactement la forme
# d'une locution — capitale, deux-points, definition — et s'en allait ouvrir un
# alinea de sous-entree, dans SOIXANTE articles sur soixante-quinze. Or ce n'est
# pas un mot de la langue : c'est une etiquette, de meme nature que le nom
# latin. On la sort donc du texte, dans son propre champ, et les deux editions
# la rendent d'une seule facon.
ETIKEDO_SIMBOLO = "simbolo kemiala"
# Les quatre graphies du libelle, pour reconnaitre le filet qui le couvrait :
# le trait le coupe court — « Simb. kem », « Simbolo kemial » — aussi souvent
# qu'il le prend en entier.
ETIKEDOJ = ("simbolo kemiala", "simb. kemiala", "simbolo kem.", "simb. kem.")
# « Simbolo » s'abrege lui aussi — « Simb. kem. Au » chez « oro », « Simb.
# kemiala : Br » chez « bromo » —, et « kem » se rencontre nu. Les quatre
# libelles se croisent librement ; le motif les prend tous.
RE_SIMBOLO = re.compile(r'[\s.,;:–-]*(\()?\s*simb(?:olo|\.)\s*kem(?:iala|\.)?'
                        r'\s*[:.]?\s*', re.I)
# Un symbole ou une formule tient en peu de signes — le plus long du livre est
# « C₁₆, H₂₆, N₂, O₁₀ ». Au-dela, ce n'est plus un symbole : chez « ruteno »
# l'article suivant, « rutino », s'est fondu dans le texte au decodage. On
# n'extrait alors RIEN, et le defaut reste visible plutot que d'etre maquille.
LONGO_SIMBOLO = 40


_SIMBOLI = None


def simboli_manuala(fichier=f"{T}/simboli.txt"):
    """Les symboles releves a l'oeil sur le fac-simile, la ou le decodage les
    a perdus. Meme cle que subvorti.txt : vedetto@image:ligno."""
    global _SIMBOLI
    if _SIMBOLI is None:
        _SIMBOLI = {}
        if os.path.exists(fichier):
            for l in open(fichier, encoding='utf-8'):
                l = l.rstrip("\n")
                if not l.strip() or l.startswith('#'):
                    continue
                p = l.split("\t")
                if len(p) >= 2 and p[0].strip() and p[1].strip():
                    _SIMBOLI[p[0].strip()] = p[1].strip()
    return _SIMBOLI


_LATINAJI = None


def latinaji_manuala(fichier=f"{T}/latinaji.txt"):
    """Les noms scientifiques redresses a l'oeil. Meme cle que simboli.txt."""
    global _LATINAJI
    if _LATINAJI is None:
        _LATINAJI = {}
        if os.path.exists(fichier):
            for l in open(fichier, encoding='utf-8'):
                l = l.rstrip("\n")
                if not l.strip() or l.startswith('#'):
                    continue
                p = l.split("\t")
                if len(p) >= 2 and p[0].strip() and p[1].strip():
                    _LATINAJI[p[0].strip()] = p[1].strip()
    return _LATINAJI


def _kodo_ne_simbolo(e):
    """Un code de langues qui EGALE le symbole chimique n'est pas un code.

    Le symbole ferme parfois l'article, sans rien derriere lui : « palado. ...
    Simbolo kemiala : Pd. » Le decodage a lu ce « Pd. » comme un code de
    langues et en a tire « portugalana, germana ». L'article n'en porte aucun.
    """
    k = (e.get('kodo') or '').strip('.').lower()
    if k and k == (e.get('simbolo') or '').strip('.').lower():
        e['kodo'] = None
        e['lingui'] = []
        if 'sen-lingua' not in e.get('drapeli', []):
            e.setdefault('drapeli', []).append('sen-lingua')


def apartigar_simbolon(e):
    """Sort le symbole chimique du texte et le met dans son champ.

    Rend 1 si un symbole a ete pose. La ou la dactylo a bien frappe l'etiquette
    mais ou le symbole ne s'est pas decode, on va le chercher dans simboli.txt,
    releve a l'oeil sur la page ; faute de l'y trouver, l'article garde son
    texte tel quel — l'etiquette sans symbole ne dit rien, mais l'effacer
    effacerait aussi la trace du manque.
    """
    man = simboli_manuala().get("%s@%d:%d" % (e.get('vedetto'),
                                              e.get('image', -1),
                                              e.get('ligno', -1)))
    S = e.get('senci') or []
    for k, t in enumerate(S):
        m = RE_SIMBOLO.search(t)
        if not m:
            continue
        resto = t[m.end():]
        if m.group(1):
            # Etiquette en incise — « ..., (simbolo kemiala : Ir) quan onu
            # renkontras... » : elle s'arrete a sa parenthese, et la phrase
            # reprend apres.
            j = resto.find(')')
            sim, suite = (resto[:j], resto[j+1:]) if j >= 0 else (resto, '')
        else:
            sim, suite = resto, ''
        sim = sim.strip(' .,;:')
        # Un texte contamine ne se laisse pas couper : chez « ruteno »
        # l'article suivant s'est fondu dans le sien, et ce qui suit
        # l'etiquette n'est pas un symbole mais des lignes entieres. On n'y
        # touche pas, meme pour y poser une lecture faite a l'oeil.
        if len(sim) > LONGO_SIMBOLO:
            continue
        if not sim and not man:
            continue
        e['simbolo'] = man or sim
        S[k] = espacar((t[:m.start()] + ' ' + suite).strip(' .,;:–-'))
        _kodo_ne_simbolo(e)
        return 1
    # L'etiquette n'est plus dans le texte : ou bien la dactylo ne l'a pas
    # frappee, ou bien un passage precedent l'en a deja sortie. Une lecture
    # faite a l'oeil s'y pose tout de meme, et corrige au besoin un symbole
    # que le decodage n'avait lu qu'a moitie — « Ca » pour « Ca F² ».
    if man and e.get('simbolo') != man:
        e['simbolo'] = man
        _kodo_ne_simbolo(e)
        return 1
    _kodo_ne_simbolo(e)
    return 0


_FILETOJ = None


def filetoj_ekartita(fichier=f"{T}/filetoj.txt"):
    """Les filets releves que l'oeil ecarte : vedetto@image:ligno -> fragments.

    Le releve prend aussi ce qui n'est pas une intention — le trait d'une ligne
    voisine, un trait qui deborde d'un mot sur le suivant. L'edition ne peut pas
    toujours le savoir : un mot plein souligne au milieu d'une definition
    ressemble a un mot cite, et le livre en cite beaucoup. Ce fichier ne fait que
    RETIRER un releve, jamais en poser un.
    """
    global _FILETOJ
    if _FILETOJ is None:
        _FILETOJ = {}
        if os.path.exists(fichier):
            with open(fichier, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or not q[0].strip() or not q[1].strip():
                        continue
                    u = q[1].strip()
                    if '{' in u or u.startswith('>'):
                        continue          # POSE : filetoj_pozita, filetoj_rendita
                    _FILETOJ.setdefault(q[0].strip(), set()).add(u)
    return _FILETOJ


_RENDITAJ = None


def filetoj_rendita(fichier=f"{T}/filetoj.txt"):
    """Les filets RENDUS au releve : vedetto@image:ligno -> fragments.

    Le trait etait la, le releve ne l'a pas vu. Rendu ici, il reprend le chemin
    ordinaire : la locution qui porte sa propre definition ouvre son alinea, le
    reste passe en italique. C'est ce dont « pseudonima » avait besoin —
    « Pseudonimo : Nomo ne-exakta » est une sous-entree, mais aucun filet ne la
    designait, et rien ne la distinguait d'une phrase.

    La ligne commence par « > » : aucun releve du livre ne porte ce signe.
    """
    global _RENDITAJ
    if _RENDITAJ is None:
        _RENDITAJ = {}
        if os.path.exists(fichier):
            with open(fichier, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or not q[1].strip().startswith('>'):
                        continue
                    u = q[1].strip()[1:].strip()
                    if u:
                        _RENDITAJ.setdefault(q[0].strip(), []).append(u)
    return _RENDITAJ


_POZITAJ = None


def filetoj_pozita(fichier=f"{T}/filetoj.txt"):
    """Les italiques posees A L'OEIL : vedetto@image:ligno -> (contexte, spans).

    L'auteur met en italique le mot qu'il CITE. Quand le releve du filet n'a rien
    rendu, l'edition ne peut pas le deviner — mais le lecteur, lui, bute :
    « La omiso di ta avan qua esas anakoluto » ne se lit pas sans savoir que
    « ta » et « qua » y sont cites, non employes.

    Le fragment porte alors des ACCOLADES autour de ce qui prend l'italique, et
    le reste est du contexte : « La omiso di {ta} avan {qua} esas anakoluto ».
    Sans lui, « qua » serait mis en italique aux trois endroits ou il parait dans
    l'article, dont deux ou il est un pronom ordinaire.
    """
    global _POZITAJ
    if _POZITAJ is None:
        _POZITAJ = {}
        if os.path.exists(fichier):
            with open(fichier, encoding='utf-8') as h:
                for l in h:
                    if l.startswith('#') or not l.strip():
                        continue
                    q = l.rstrip('\n').split('\t')
                    if len(q) < 2 or '{' not in q[1]:
                        continue
                    brut = q[1].strip(); kun = ''; spans = []; deb = None
                    for c in brut:
                        if c == '{':
                            deb = len(kun)
                        elif c == '}':
                            if deb is not None: spans.append((deb, len(kun)))
                            deb = None
                        else:
                            kun += c
                    if kun and spans:
                        _POZITAJ.setdefault(q[0].strip(), []).append((kun, spans))
    return _POZITAJ


def _rekolar(subl, textoj):
    """Le filet coupe par une fin de ligne : ses deux moities n'en font qu'une.

    La dactylo souligne « Kreto-krayono » ; la ligne casse au milieu du mot, et
    le releve rend « Kreto-kra- » puis « yono ». Cherches tels quels, aucun des
    deux ne se retrouve dans le texte recolle : la locution qu'ils designent
    n'etait plus reconnue, et les deux moities finissaient parmi les fragments
    non places. On les recolle quand la forme jointe, elle, se trouve dans le
    texte — avec ou sans le trait d'union, selon ce que le recollage a decide.

    Un tiret final n'annonce pas toujours une coupure : « -ez- » et « auto - »
    en portent un qui leur appartient. La condition est donc la MEME que pour
    poser l'italique — le morceau joint doit se retrouver dans le texte —, et
    ce qui ne s'y retrouve pas reste tel quel.
    """
    out=[]; i=0
    while i < len(subl):
        u=subl[i]
        if u.endswith('-') and i+1 < len(subl):
            for j in (u[:-1]+subl[i+1], u+subl[i+1]):
                if any(_trovar(j, t) for t in textoj):
                    out.append(j); i+=2; break
            else:
                out.append(u); i+=1
        else:
            out.append(u); i+=1
    return out


def strukturizar(e):
    """Decoupe chaque sens en un corps et, s'il y a lieu, ses sous-entrees.

    « proporciono » porte quatre locutions dans son second sens, chacune avec
    sa propre definition. Les couler dans un seul paragraphe les rendait
    introuvables ; on les detache, avec leur qualificatif de domaine.
    """
    subl=_rekolar(sublineajoj(e), e.get('senci') or [])
    _for=filetoj_ekartita().get("%s@%d:%d" % (e.get('vedetto'),
                                              e.get('image', -1), e.get('ligno', -1)))
    if _for: subl=[u for u in subl if u not in _for]
    for u in filetoj_rendita().get("%s@%d:%d" % (e.get('vedetto'),
                                                e.get('image', -1),
                                                e.get('ligno', -1)), ()):
        if u not in subl: subl.append(u)
    e['sublineita']=subl
    strukt=[]; n_sub=0
    for t in (e.get('senci') or []):
        trov=[]
        for m in RE_LOKUCO.finditer(t):
            loko=m.group(1)
            if not any(_kongruas(loko, u) for u in subl): continue
            # Un seul mot, sans trait d'union, etranger a la vedette : ce n'est
            # pas une locution mais une GLOSE — « moloso. ... – Nun : grosa
            # gardo-hundo », ou « Nun » est l'adverbe « maintenant ». La
            # capitale et le deux-points ne suffisent pas a la distinguer ; le
            # lien avec la vedette, si. Les vraies locutions d'un seul mot sont
            # soit des composes — « mar-baseno », « dento-krono » —, soit des
            # derives de la vedette — « acido » sous « acida ».
            if (len(loko.split()) == 1 and '-' not in loko
                    and not _citas_vedeton(loko, e.get('vedetto') or '')):
                continue
            trov.append((m.start(1), m.end(), loko, None))
        pris={x[0] for x in trov}
        for m in RE_LOKUCO_KRAMPA.finditer(t):
            loko=m.group(1)
            if m.start(1) in pris: continue
            if not any(_kongruas(loko, u) for u in subl): continue
            if not (loko[:1].isupper()
                    or _citas_vedeton(loko, e.get('vedetto') or '')): continue
            trov.append((m.start(1), m.end(), loko, (m.start(), _fermo(t, m.start()))))
        for m in RE_SUBARTIKLO.finditer(t):
            loko=m.group(1)
            if m.start(1) in pris or any(x[0] == m.start(1) for x in trov): continue
            if not any(_kongruas(loko.lstrip('*'), u) for u in subl): continue
            trov.append((m.start(1), m.end(), loko, (m.start(), _fermo(t, m.start()))))
        trov.sort()
        if not trov:
            strukt.append({"teksto": t, "sub": []}); continue
        # Une locution entre parentheses commence a sa parenthese OUVRANTE : le
        # signe appartient a la locution, non au texte qui la precede.
        deb=[x[3][0] if x[3] else x[0] for x in trov]
        sub=[]; suite=[]
        for i,(a,apres,loko,kr) in enumerate(trov):
            fin=deb[i+1] if i+1 < len(trov) else len(t)
            if kr and kr[1] is not None and kr[1] < fin:
                # La sous-entree s'arrete a la parenthese qui la ferme. Ce qui
                # suit reprend la phrase du sens — « (en vehilo publika : ...)
                # La komizo di qua la rolo... » — et retourne donc au corps.
                suite.append(t[kr[1]+1:fin]); fin=kr[1]
            sub.append({"loko": loko, "fako": "", "teksto": t[apres:fin].strip()})
        tete=t[:deb[0]]
        # Le qualificatif colle a la locution qui suit, non au sens precedent.
        for i in range(len(sub)):
            src = tete if i == 0 else sub[i-1]["teksto"]
            m=RE_KVAL.search(src)
            if m:
                q=m.group(0).strip(" -\u2013")
                src=src[:m.start()]
                sub[i]["fako"]=q
                if i == 0: tete=src
                else: sub[i-1]["teksto"]=src.rstrip(" -\u2013,;")
        # Un numero d'enumeration reste seul en tete : il ouvre la premiere
        # sous-entree plutot que de faire un sens vide.
        tete=tete.strip(" -\u2013;,")
        m=RE_NUMERO.match(tete.strip()) if tete else None
        if m and len(tete.strip()) <= 3:
            sub[0]["fako"]=(tete.strip()+" "+sub[0]["fako"]).strip(); tete=""
        # Le texte qui suivait la parenthese se recolle au corps du sens, la
        # parenthese otee. On le fait EN DERNIER : le qualificatif de tete et le
        # numero d'enumeration se lisent a la fin du texte qui PRECEDE, et une
        # reprise collee avant les aurait caches.
        if suite:
            tete=espacar(re.sub(r'\s+', ' ',
                                (tete + " " + " ".join(suite))).strip())
        n_sub += len(sub)
        strukt.append({"teksto": tete, "sub": sub})
    for b in strukt:
        b['teksto']=majuskla_komenco(b['teksto'])
        for x in b['sub']:
            x['loko']=minuskla_lokuco(x['loko'])
            # Le tiret qui introduisait la locution SUIVANTE reste au bout du
            # corps de la precedente — « ... relate Suno. – ». Il n'annonce
            # plus rien, la locution ayant pris son alinea.
            x['teksto']=x['teksto'].rstrip(" -–,;")
            if not x['fako']:
                mk=RE_KVAL_KAPO.match(x['teksto'])
                if mk:
                    x['fako']=mk.group(0).strip()
                    x['teksto']=x['teksto'][mk.end():].lstrip(' .,;:')
            x['teksto']=majuskla_komenco(x['teksto'])
            # Le qualificatif est garde NU, comme le champ `fako` de l'article :
            # ce sont les editions qui posent les parentheses. Sans cela le
            # domaine d'une locution — pris entre parentheses dans le texte —
            # et celui d'un article rattache — pris dans le champ — ne
            # s'ecrivaient pas de la meme facon.
            x['fako']=uniformigar(x['fako'].strip().strip('()').strip())
    e['strukt']=strukt
    # Ce qui reste souligne sans etre une locution : le domaine, le nom latin,
    # le mot cite. L'edition le rend en italique, la ou il se retrouve.
    lok={x["loko"].lower() for b in strukt for x in b["sub"]}
    textoj=[b["teksto"] for b in strukt] + [x["teksto"] for b in strukt for x in b["sub"]]
    kur=[]; dub=[]; vu=set()
    for u in subl:
        if u.lower() in lok: continue
        pose=False
        alt=alia_formo(u)
        # Le releve est BRUT, le texte est typographie : les points de
        # suspension y sont devenus le caractere unique, et l'affixe qui les
        # suit s'en est detache. « lore...lore » (lor), « trans., por...-eso »
        # (elektar) ne s'y retrouvaient plus, et le filet passait pour non
        # place. On cherche donc aussi la forme typographiee du releve.
        if not alt and elipso(u) != u:
            alt=elipso(u)
        for t in textoj:
            m=_trovar(u, t); mot=u
            if not m and alt:
                m=_trovar(alt, t); mot=alt
            if not m: continue
            # Le filet ne couvre souvent qu'une PARTIE de la parenthese : la
            # dactylo souligne « aludante persono » mais coupe son trait au
            # bout de la ligne. On met en italique la parenthese entiere —
            # c'est elle, le qualificatif — et les deux moities se recollent.
            g=_parentezo(t, m.start(), m.end())
            if g is None and (len(mot) < 3 or _nur_motouti(mot)):
                dub.append(u); continue
            v=g if g else mot
            if v.lower() not in vu: vu.add(v.lower()); kur.append(v)
            pose=True
        if not pose and u not in dub: dub.append(u)
    e['kursiva']=kur
    _poz=filetoj_pozita().get("%s@%d:%d" % (e.get('vedetto'),
                                            e.get('image', -1), e.get('ligno', -1)), ())
    for b in strukt:
        b['teksto_k']=marki(b['teksto'], kur, _poz)
        for x in b['sub']:
            x['teksto_k']=marki(x['teksto'], kur, _poz)
    # Un fragment absent du corps n'est pas douteux s'il a trouve sa place
    # ailleurs : domaine, nom latin, locution — fut-ce une PART de locution.
    # Le filet de « radiko » se rompt en fin de ligne et rend « Extraktar
    # radiko, quadrata » puis « kubala, di nombro » : la seconde moitie ne se
    # retrouve nulle part telle quelle, et pourtant elle est placee, la
    # locution ayant pris son alinea.
    # Le souligne porte la forme que l'auteur a ECRITE, le champ celle que
    # l'edition retient : « medicino » sur la page, « medic. » dans le champ. On
    # compare donc a la ponctuation pres, chaque moitie du champ et chaque
    # domaine enumere comptant a part — et de part et d'autre, car le souligne
    # peut etre plus court que le domaine (le filet s'est rompu en fin de ligne)
    # comme plus long (l'edition a abrege). Dans ce second sens on exige quatre
    # lettres, pour qu'un domaine bref — « per », « pri » — ne couvre pas
    # n'importe quel fragment.
    fakoj=set()
    for _f in [(e.get('fako') or '')] + [x['fako'] for b in strukt for x in b['sub']]:
        if not _f: continue
        for _part in _f.split(') ('):
            for _p in RE_KOMPONO.split(_part):
                _p=_plata(_p)
                if _p: fakoj.add(_p)
        _p=_plata(_f)
        if _p: fakoj.add(_p)
    # « prosodio » et « prozodio » ne se contiennent pas l'un l'autre : la table
    # des variantes le dit, la comparaison ne peut pas le deviner.
    fakoj |= {_plata(v) for f in list(fakoj) for v in DOMENI_VARIANTOJ.get(f, ())}
    # Le nom scientifique donne parfois DEUX formes en une : « rubus caesius,
    # rubus fructicosus », « conium maculatum, e speco di cicuta ». Le filet, lui,
    # couvre chaque nom a part : cherche au caractere pres, le second passait
    # pour un souligne non place. On accepte donc le MORCEAU, a partir de quatre
    # lettres.
    lat={x.lower() for x in (e.get('latina') or [])}
    latp={_plata(x) for x in lat}
    lokoj=[x['loko'] for b in strukt for x in b['sub']]
    e['dubinda']=[u for u in dub
                  if not any(_plata(u) and (_plata(u) in f
                                            or (len(f) >= 4 and f in _plata(u)))
                             for f in fakoj)
                  and u.lower() not in lat
                  and not any(_preskau_en(u.lower(), x) for x in lat)
                  and not any(len(_plata(u)) >= 4 and _preskau_en(_plata(u), f)
                              for f in latp)
                  and not any(_kongruas(u, L) or _enhavas(L, u) for L in lokoj)
                  # L'etiquette du symbole chimique a quitte le texte pour son
                  # champ : le filet qui la couvrait est place, non douteux.
                  # Le trait la coupe souvent court — « Simbolo kem »,
                  # « Simbolo kemial » — ou n'en prend que la fin —
                  # « kemiala » : on accepte donc tout morceau de l'etiquette,
                  # a partir de trois lettres pour ne pas happer n'importe quoi.
                  and not (e.get('simbolo') and
                           (_enhavas(ETIKEDO_SIMBOLO + ' ' + e['simbolo'], u)
                            or (len(u.strip()) >= 3
                                and any(u.lower().strip(' .:') in E
                                        for E in ETIKEDOJ))))]
    return n_sub


# Mots-outils : un filet qui ne couvre qu eux est un artefact du releve des
# soulignements, non une intention de l auteur.
# Les mots-outils : ceux qu'un filet ne designe jamais pour eux-memes. Un
# soulignement qui ne couvre QUE ceux-la n'est pas une marque de l'auteur mais
# une trace — le trait d'une ligne voisine, ou un releve qui a deborde.
# « absinto » portait « ek la » en italique au milieu de sa definition.
#
# La liste est CLOSE : articles, prepositions, conjonctions, pronoms et
# correlatifs, plus les formes de « esar ». Un mot plein n'y entre pas, meme
# court : « Ido » chez « logiko », « ohm » chez « volto », « tri » chez
# « tri- » sont des mots cites, et gardent leur italique.
#
# Quatre mots-outils en sont retires, parce que le livre les CITE quelque part
# et que le filet y est une vraie marque : « ante » chez « avan » (« kontre ke
# ante relatas tempo »), « avan » et « dop » chez « retro- » (« movo de avan ad
# dop »), et « que » chez « enklitiko », ou il est latin — « L. que en neque ».
MALGRANDA={'la','lo','de','da','di','en','per','sur','a','ad','ab','ek','ye',
           'che','apud','cirkum','dum','exter','inter','kontre',
           'malgre','preter','segun','sub','super','til','trans','ultre','vers',
           'kun','pri','pro','po','sen','por','pos',
           'qua','quan','quo','quon','qui','quin','ula','ulo','ulu','irga',
           'lu','li','ol','olu','ilu','elu','onu','me','tu','vu','ni','vi',
           'su','mea','tua','vua','nia','via','lua','sua','lia','olua',
           'ica','ita','ico','ito','ta','to','ca','co',
           'e','ed','o','od','ma','se','ke','nam','do','nek','ne',
           'kom','anke','tre','plu','min','nun','olim','hike','ibe','ja','mem',
           'nur','tro','tam','tale','quale','kande','ube','lore','tande',
           'esas','esis','esos','esus','esar','e c'}


def _nur_motouti(u):
    """Le fragment ne couvre-t-il QUE des mots-outils ?"""
    # « e c » — « e cetera » — s'ecrit en deux morceaux dont le second n'est
    # pas un mot : on l'admet entier.
    if u.strip().lower() in MALGRANDA: return True
    mots=[m.strip('.,;:()«»\'’\u201c\u201d "').lower() for m in u.split()]
    mots=[m for m in mots if m]
    return bool(mots) and all(m in MALGRANDA for m in mots)


def _preskau_en(u, f):
    """Le fragment se retrouve-t-il dans f, a UNE lettre pres ?

    Le releve du filet porte la lecture de la MACHINE ; le champ `latina`, lui,
    a pu etre redresse a l'oeil — « myrmedophaga » rendu « myrmecophaga », que
    la vedette « mirmekofago » prouve. Cherche au caractere pres, le filet ne se
    retrouvait plus, et le nom scientifique passait pour un souligne non place.
    Une lettre d'ecart, c'est exactement ce qu'une correction de lecture change ;
    on exige quatre lettres pour qu'un fragment bref ne couvre pas n'importe quoi.
    """
    if len(u) < 4 or len(u) > len(f):
        return False
    return any(sum(1 for a, b in zip(u, f[i:i+len(u)]) if a != b) <= 1
               for i in range(len(f) - len(u) + 1))


def _trovar(u, t):
    """L occurrence du fragment souligne dans le texte, l espacement libre."""
    if not u.strip(): return None
    # Sans egard a la casse : l'auteur ecrit « (Anke metaf.) », l'edition
    # abaisse l'initiale des domaines, et le fragment releve sur la grille ne
    # se retrouverait plus dans le texte.
    # L'asterisque du mot non officiel se pose APRES le releve du filet, et
    # le trait de la dactylo la couvre sans la connaitre : « pri grandoro » ne
    # se retrouvait plus dans « (pri *grandoro) ». On la laisse donc passer
    # entre les mots — devant le premier, la borne de gauche l'admet deja.
    # _tuti(), qui POSE l'italique, suit la meme regle.
    mo=re.compile(r'(?<![A-Za-z\u00c0-\u00ff])'
                  + r'\s+\*?'.join(re.escape(w) for w in u.split())
                  + r'(?![A-Za-z\u00c0-\u00ff])', re.I)
    return mo.search(t)


def _parentezo(t, a, b):
    """Si le fragment est dans une parenthese, cette parenthese entiere."""
    i=t.rfind('(', 0, a)
    if i < 0: return None
    j=t.find(')', b-1)
    if j < 0: return None
    if '(' in t[i+1:j] or ')' in t[i+1:a]: return None
    if j-i > 70: return None
    return t[i:j+1]

def rataching_subvortoj(ent, fichier=f"{T}/subvorti.txt"):
    """Rattache un article a celui dont l'auteur l'a fait dependre.

    Le rattachement ne DEGRADE pas l'article : il garde son domaine, son code
    de langues et sa page. Il change seulement de place — au lieu d'ouvrir sa
    propre entree, il se range sous celle dont il derive, comme les locutions.
    Il reste trouvable par son nom : les exportations rangent les locutions
    parmi les formes cherchables, au meme rang qu'une vedette.
    """
    if not os.path.exists(fichier): return 0
    couples=[]
    for l in open(fichier,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith('#'): continue
        a,_,b=l.partition("\t")
        couples.append((a.strip(), b.strip()))
    if not couples: return 0
    par={}
    for e in ent: par["%s@%d:%d" % (e['vedetto'], e['image'], e['ligno'])]=e
    otar=set(); n=0
    for cle, clep in couples:
        f=par.get(cle); m=par.get(clep)
        if f is None or m is None:
            print("  rattachement sans cible : %s -> %s" % (cle, clep)); continue
        blocs=f.get('strukt') or []
        korpo=" ".join(b['teksto'] for b in blocs if b['teksto']).strip()
        korpo_k=" ".join(b.get('teksto_k') or b['teksto'] for b in blocs
                         if b['teksto']).strip()
        if not korpo: continue
        cible=(m.get('strukt') or [None])[-1]
        if cible is None: continue
        cible['sub'].append({"loko": f['vedetto'], "fako": f['fako'] or "",
                             "teksto": korpo, "teksto_k": korpo_k,
                             "kodo": f.get('kodo') or "",
                             "lingui": f.get('lingui') or []})
        m['sublineita']=(m.get('sublineita') or []) + (f.get('sublineita') or [])
        otar.add(id(f)); n+=1
    if otar:
        ent[:]=[e for e in ent if id(e) not in otar]
    return n


def konstrui():
    pages,corr,filetoj = charger_texte()
    brut=decouper(pages,corr,filetoj)
    # Deux passes : la premiere donne le lexique des vedettes, la seconde s'en
    # sert pour trancher les traits d'union tombes sur une fin de ligne.
    # Le lexique sert a trancher les traits d'union de fin de ligne : une
    # vedette d'une lettre y attesterait n'importe quel fragment.
    lex={e['vedetto'].lower() for e in (analizar(x) for x in brut)
         if e_ok(e) and len(e['vedetto']) >= 2}
    n0=len(brut); brut=dividar(brut, lex)
    if len(brut)>n0: print("articles separes d'une ligne partagee : %d"%(len(brut)-n0))
    ent=[analizar(e, lex) for e in brut]
    n=appliquer_jugements(ent)
    if n: print("jugements lexicaux appliques : %d occurrences"%n)
    n=typographio(ent)
    if n: print("sens retouches typographiquement : %d"%n)
    n=corriger_vedettes(ent)
    if n: print("vedettes corrigees a la main : %d"%n)
    # Le drapeau de finale se lit SUR LA VEDETTE : corrigee ici, il doit se
    # relire. « borc » devenu « boro », « fenikulc » devenu « fenikulo », la
    # finale impossible a disparu — mais le drapeau qui la signalait restait,
    # et la liste de travail designait un travail deja fait. Le drapeau d'ordre,
    # lui, se recalcule deja en fin de chaine, pour la meme raison.
    n=0
    for e in ent:
        v=e.get('vedetto') or ''
        ok=_finalo_ok(e)
        if ok and 'finalo-nekustumala' in e['drapeli']:
            e['drapeli'].remove('finalo-nekustumala'); n+=1
        elif v and not ok and 'finalo-nekustumala' not in e['drapeli']:
            e['drapeli'].append('finalo-nekustumala'); n+=1
    if n: print("drapeaux de finale relus apres correction : %d"%n)
    n=corriger_vorti(ent)
    if n: print("mots corriges dans les definitions : %d"%n)
    import relire as _rel
    n,r=_rel.appliquer(ent)
    if n or r: print("relecture des definitions : %d corrections posees, %d refusees"%(n,r))
    # La relecture rend le domaine tel qu'il se LIT sur la page — avec sa
    # majuscule, et sans le point que le tapuscrit n'a pas frappe. Le champ, lui,
    # est mis en minuscules et son abreviation pointee bien plus haut, AVANT
    # cette correction : « (ariktekt.) » corrige en « arkitekt » ressortait donc
    # nu quand ses trente voisins etaient pointes. On repasse les deux
    # normalisations derriere la correction ; elles sont idempotentes.
    for e in ent:
        if e.get('fako'): e['fako']=kompozita(elipso(uniformigar(minuskligi(pointi(e['fako'])))))
    # La relecture pose des chaines relevees avant la typographie : on repasse
    # l'espacement derriere elle. espacar() est idempotente.
    for e in ent:
        S=e.get('senci') or []
        for k,t in enumerate(S):
            # Ponctuation orpheline en tete de sens : elle vient d'une coupure
            # de l'original, non du texte. « titrar » commencait par un point.
            S[k]=kompozita(elipso(ekvilibrigi_parentezojn(pointi_abrevo(fermi_parentezon(
                fermi_kvalifikilon(orfa_parentezo(formuli(cifri(pointi_sencoj(
                    surcharge(espacar(netigar_punktuo(t)))))))))).lstrip('.,;:) ').strip())))
    # (cifri et formuli n'interviennent qu'ici, une fois la relecture posee)
    # Second passage des corrections a l'oeil. Une ligne de vorti.txt ecrite
    # d'apres le texte RENDU ne pouvait pas s'appliquer plus haut : « de l til
    # 10 litri » (bidono) porte un 10 que cifri n'avait pas encore tire du
    # « lO » de la dactylo, et la correction ne prenait jamais — en silence.
    # La fonction est idempotente : une correction deja posee ne trouve plus sa
    # forme fautive et ne fait rien.
    n=corriger_vorti(ent)
    if n: print("mots corriges apres la mise en chiffres : %d"%n)
    # Second rattrapage du code de langues. Celui de l'analyse passe AVANT la
    # typographie ; quand la fin de ligne portait encore une scorie — un point
    # isole chez « ganso », une ponctuation manquante chez « rodar » — le code
    # ne s'ancrait pas, et l'article passait pour « sen-lingua » en gardant son
    # code dans le texte. Repasse ici, il s'ancre.
    n=0
    for e in ent:
        if e.get('kodo') or not e.get('senci'): continue
        mk=re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][-1])
        li=_lire_code(mk.group(1)) if mk else None
        if not li: continue
        e['lingui']=li; e['kodo']=mk.group(1)
        q=e['senci'][-1][:mk.start()].rstrip(' -–.,;:')
        if q: e['senci'][-1]=q
        else: e['senci'].pop()
        if 'sen-lingua' in e['drapeli']: e['drapeli'].remove('sen-lingua')
        n+=1
    if n: print("codes de langues rattrapes apres la typographie : %d"%n)
    # Le code n'est pas toujours au bout du DERNIER sens. L'auteur l'a parfois
    # pose, puis a ajoute un sens apres coup : « arniko. I. Planto aromata...
    # - L. arnica montana. - DEFIS. II. Medikamento liquida... ». Le code reste
    # alors au milieu de l'article, l'article passe pour « sen-lingua », et le
    # lecteur voit « DEFIS » dans une definition. On le releve la aussi — sur le
    # DERNIER sens qui en porte un, et pour les seuls articles qui n'en ont pas.
    n=0
    for e in ent:
        if e.get('kodo') or not e.get('senci'): continue
        for k in range(len(e['senci'])-1, -1, -1):
            mk=re.search(r'(?:[-–.,()*]|\s)\s*([A-Za-z]{1,12})\s*\.?\s*$', e['senci'][k])
            li=_lire_code(mk.group(1)) if mk else None
            if not li: continue
            e['lingui']=li; e['kodo']=mk.group(1)
            q=e['senci'][k][:mk.start()].rstrip(' -–.,;:')
            if q: e['senci'][k]=q
            else: e['senci'].pop(k)
            if 'sen-lingua' in e['drapeli']: e['drapeli'].remove('sen-lingua')
            n+=1; break
    if n: print("codes de langues releves hors du dernier sens : %d"%n)
    n=ordinigi_kodojn(ent)
    if n: print("codes de langues remis dans l'ordre du livre : %d"%n)
    n=steligar(ent)
    if n: print("mots non officiels marques la ou ils etaient nus : %d"%n)
    # Article commence en bas de page, abandonne, puis RECOMMENCE en tete de la
    # page suivante. « ampère » est le seul cas du livre : la premiere version
    # s'arrete net, sans code de langues ; la seconde est complete. L'edition de
    # lecture ne garde que celle-ci — le fac-simile, lui, conserve les deux,
    # puisqu'il rend la page telle qu'elle fut frappee.
    der={}; unua={}
    for e in ent:
        if e['ligno'] >= der.get(e['image'], (-1,))[0]: der[e['image']]=(e['ligno'], e)
        if e['ligno'] <= unua.get(e['image'], (10**6,))[0]: unua[e['image']]=(e['ligno'], e)
    fals=set()
    for pg,(_, a) in der.items():
        b = unua.get(pg+1, (None,None))[1]
        if b is not None and a['vedetto'] == b['vedetto'] and not a['kodo'] and b['kodo']:
            fals.add(id(a))
    if fals:
        ent=[e for e in ent if id(e) not in fals]
        print("faux departs de bas de page ecartes : %d"%len(fals))
    n0=len(ent); ent=[e for e in ent if e_ok(e)]
    if len(ent)<n0: print("renvois d'errata ecartes : %d"%(n0-len(ent)))
    # Definition coupee net en bas de page : le scan a rogne la derniere ligne.
    # Quatre articles finissent ainsi sur un mot-outil, sans code de langues, et
    # leur suite n'est sur aucune page. On ne l'invente pas — on le dit.
    RE_OUTIL=re.compile(r"(?<![A-Za-zÀ-ÿ])(?:di|de|la|ye|ad|en|kun|per|sur|qua|quan"
                        r"|quon|pri|po|od|ek|da|kom|ma|nek|sen)$")
    der={}
    for e in ent: 
        if e['ligno'] >= der.get(e['image'], (-1,None))[0]: der[e['image']]=(e['ligno'], e)
    for _,e in der.values():
        t=" ".join(e['senci']).rstrip()
        if t and not e['kodo'] and RE_OUTIL.search(t):
            e['drapeli'].append('tranchita-che-pagino-fino')
    # Numerotation des sens. L'edition de lecture les numerote elle-meme, 1, 2,
    # 3 : garder « I. », « II. » dans le texte ferait double emploi, et
    # l'original est irregulier — « iambo » melange deux niveaux, « tribono »
    # melange chiffres romains et arabes. On retire donc le numero de tete.
    # Trois sens ne contiennent QUE leur etiquette de domaine, sans definition
    # (« (metriko antiqua) ») : elle se rattache au sens suivant, qu'elle
    # qualifie, plutot que de rester seule.
    # La virgule remplace parfois le point apres le numero — « I, (olim). ».
    # Elle n'est admise QU'APRES un chiffre romain suivi d'une majuscule ou
    # d'une parenthese : « l, OOO, OOO » (biliono) et « 10 , od oktiliono »
    # (noniliono) sont des nombres, non des numeros de sens.
    # « 1.000 » n'est pas un sens numerote mais le nombre mille : sans cette
    # garde, « mil » perdait son « 1. » et se definissait par « 000 ».
    # Le numero sans son point — « III veziketo » — se retire aussi, sinon il
    # ouvrirait le sens que la coupure vient d'isoler.
    RE_NUM=re.compile(r'^(?:(?:I{1,3}|IV|VI{0,3}|IX|X|[l\d]\d?)[.)](?!\d)\s*'
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X),\s*(?=[A-ZÀ-Ý(])'
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X)\s+(?=[A-Za-zÀ-ÿ])'
                      # Le numero suivi de la parenthese du qualificatif —
                      # « I (zool.) Mamifero... » chez « leono », six articles.
                      # L'espace y est facultative : « reklamacar.I(netrans.) ».
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X)\s*(?=\())')
    RE_ETIQ=re.compile(r'^\([^()]{1,40}\)\.?$')
    n_num=0
    for e in ent:
        S=[]
        for t in e.get('senci') or []:
            # Numerotation IMBRIQUEE : « III. 1. Deklarar... ». Un seul retrait
            # n'ote que le niveau superieur. On boucle, borne a trois tours.
            u=t
            for _ in range(3):
                w=RE_NUM.sub('', u).strip()
                if w == u: break
                u = w
            if u != t: n_num += 1
            # « I » ou « II » seuls, sans definition : un numero orphelin que le
            # decoupage a pris pour un sens. Il ne dit rien.
            if re.fullmatch(r'(?:I{1,3}|IV|VI{0,3}|IX|X)', u): u=''
            # Point double apres le numero — « titrar. I..(teknol.) ». Le
            # retrait du numero laisse le second, orphelin en tete de sens.
            # Le tiret separait les sens dans l'original — « vunduro. II. -
            # (religio kristana). Marko... ». Le numero ote, il reste en tete
            # et n'annonce plus rien. Il empechait en outre les editions de
            # reconnaitre la parenthese de tete comme un domaine, et « stigmato
            # » perdait l'italique de « (religio kristana) ».
            u = re.sub(r'^[.,;:)\s–-]+', '', u)
            u = espacar(u)
            S.append(u)
        fus=[]
        for i,t in enumerate(S):
            if RE_ETIQ.match(t) and i+1 < len(S):
                S[i+1] = t.rstrip('.') + ' ' + S[i+1]
                continue
            if t: fus.append(t)
        e['senci']=fus
    if n_num: print("numeros de sens retires : %d"%n_num)
    # Les soulignements de l'auteur, releves sur la grille : ils donnent les
    # locutions — sous-entrees a part entiere — et ce qui va en italique.
    n_maj=0
    for e in ent:
        S=e.get('senci') or []
        for k,t in enumerate(S):
            u=majuskla_komenco(t)
            if u != t: S[k]=u; n_maj += 1
    if n_maj: print("sens rendus a la capitale initiale : %d"%n_maj)
    n_sim=sum(apartigar_simbolon(e) for e in ent)
    if n_sim: print("symboles chimiques mis en champ : %d"%n_sim)
    n_sub=sum(strukturizar(e) for e in ent)
    n_kur=sum(1 for e in ent if e.get('kursiva'))
    print("locutions detachees : %d ; articles avec un souligne : %d"%(n_sub, n_kur))
    for e in ent: e.pop('filetoj', None)
    n_rat=rataching_subvortoj(ent)
    if n_rat: print("articles rattaches en sous-entree : %d"%n_rat)
    drapeli_ordino(ent)
    return ent

# ---------------------------------------------------------------------------
# Couche des jugements lexicaux.
#
# Les corrections rendues par le jugement etaient ecrites dans le JSONL. Or
# edition.py le reconstruit depuis le fac-simile : la reconstruction suivante
# les effacait toutes, sans bruit. On les applique donc EN FIN DE CHAINE, a
# partir des fichiers de reponses, comme filets.pkl et debuts.pkl le sont pour
# le fac-simile. Une correction posee une fois est ainsi acquise.
JUGEMENTS = [(f"{T}/juger/fiches.json",  f"{T}/juger/reponses"),
             (f"{T}/sens/fiches.json",   f"{T}/sens/reponses")]

def cifri(t):
    """Chiffres lus comme des lettres : « lOO » pour « 100 », « 2O » pour 20.

    La machine n'avait pas de touche 1 ni de touche 0 distinctes du « l » et du
    « O » — usage courant des dactylos de l'epoque. Mais on ne peut pas
    convertir a l'aveugle : dans « Al2O3 », « Fe2 O3 », « C6 H10 O5 », le O est
    l'OXYGENE, et dans « De punto fixa O » c'est le nom d'un point. On ne
    convertit donc que dans un contexte sans ambiguite : jeton commencant par
    « l », chiffre suivi de « O » ou de « l » sans espace, et suite d'au moins
    trois « O » — que nulle formule ne porte.
    """
    def _jeton(m):
        return m.group(0).replace('l', '1').replace('O', '0')
    t = re.sub(r'(?<![A-Za-zÀ-ÿ0-9])l[lO0-9]+(?![A-Za-zÀ-ÿ])', _jeton, t)
    t = re.sub(r'(?<=\d)[lO](?![A-Za-zÀ-ÿ0-9])', _jeton, t)
    t = re.sub(r'O{3,}', lambda m: '0' * len(m.group(0)), t)
    # Numero d'enumeration isole : « ... indikar : l. objekto plu proxima ».
    # Le « l » y tient lieu de 1. On exige le deux-points qui ouvre la liste.
    t = re.sub(r'(?<=[:;]\s)l(?=[.)]\s)', '1', t)
    # « (l) » ouvre une enumeration entre parentheses : c'est le chiffre 1.
    t = re.sub(r'\(l\)', '(1)', t)
    # Le degre : la machine n'avait pas le signe et frappait un « o ».
    t = re.sub(r'(?<=\d)o(?=\s*(?:C\b|Celsius))', '\u00b0', t)
    # « lOOOmetri » : la dactylo a soude le nombre a son unite. On exige trois
    # chiffres et trois minuscules, ce qui epargne les formules — « C6H4 » n'a
    # qu'une lettre, et elle est capitale.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])(\d{3,})(?=[a-zà-ÿ]{3,})', r'\1 ', t)
    return t


_SUB = str.maketrans('0123456789', '\u2080\u2081\u2082\u2083\u2084\u2085\u2086\u2087\u2088\u2089')
# L'algebre s'annonce par son enonce, non par ses signes : « M' = aluminio »
# chez aluno est une legende, pas une equation.
_SUP = str.maketrans('0123456789', '\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079')
_ALGEBRO = re.compile(r'\bequaciono\b|\bkoeficient|\bgrado\b.{0,20}\bduesma\b'
                       r'|\brelato\b|\bkubo\b|kalorizala')
_FORMULO = re.compile(r'(?<![A-Za-zÀ-ÿ])((?:[A-Z][a-z]?\d*[\s.]{0,2}){2,})(?![a-zà-ÿ])')


def formuli(t):
    """Indices des formules chimiques : « H2 O » devient « H\u2082O ».

    La machine ne descendait pas les chiffres : elle les frappait sur la ligne,
    et separait souvent les symboles d'une espace pour la lisibilite. On rend
    l'indice et on recolle. Deux garde-fous : il faut au moins deux symboles et
    un chiffre — sans quoi « DEFIRS » ou « I. La » passeraient pour une
    formule — et un « La » initial suivi d'une espace est l'article ido, non
    le lanthane : « La C5 H4 N4 O2 quan kontenas... ».
    """
    def _un(m):
        c = m.group(1)
        if not re.search(r'\d', c) or len(re.findall(r'[A-Z]', c)) < 2:
            return c
        tete = ''
        ml = re.match(r'La\s+(?=[A-Z])', c)
        if ml:
            tete = ml.group(0); c = c[ml.end():]
            if len(re.findall(r'[A-Z]', c)) < 2 or not re.search(r'\d', c):
                return m.group(1)
        q = c[len(c.rstrip()):]; c = c.rstrip()
        c = re.sub(r'(?<=[A-Za-z0-9])\s+(?=[A-Z])', '', c)
        c = re.sub(r'(?<=[A-Za-z])(\d+)', lambda x: x.group(1).translate(_SUB), c)
        return tete + c + q
    t = _FORMULO.sub(_un, t)
    # Cas que le motif principal ne prend pas, faute de deux symboles voisins :
    # le chiffre qui suit une parenthese — « (CH\u2083)2 », « (OH)3 » — celui
    # qui suit un symbole amorce — « M'2 » — et le symbole isole precede d'un
    # coefficient — « 24 H2 ». On epargne l'algebre, ou le chiffre est un
    # EXPOSANT et non un indice : « ax2 + bx + c = 0 » chez diskriminanto,
    # « Ax2 + 2 Bxy » chez koniko. Les deux se reconnaissent a leur enonce.
    if _ALGEBRO.search(t):
        # En algebre le chiffre est un EXPOSANT : « ax2 + bx + c = 0 » se lit
        # ax\u00b2. Meme chose pour l'unite elevee a une puissance, « metro3 ».
        return re.sub(r'(?<=[A-Za-z])([23])(?![\d.,])',
                      lambda m: m.group(1).translate(_SUP), t)
    t = re.sub(r'\((\[A-Z][a-z]?)(\d+)\)',
               lambda m: '(' + m.group(1) + m.group(2).translate(_SUB) + ')', t)
    t = re.sub(r'\(([A-Z][a-z]?)(\d+)\)',
               lambda m: '(' + m.group(1) + m.group(2).translate(_SUB) + ')', t)
    t = re.sub(r'(?<=\))(\d+)', lambda m: m.group(1).translate(_SUB), t)
    t = re.sub(r"(?<=')(\d+)", lambda m: m.group(1).translate(_SUB), t)
    t = re.sub(r'(?<=\s)([A-Z][a-z]?)(\d+)(?!\d)',
               lambda m: m.group(1) + m.group(2).translate(_SUB), t)
    return t


_SUR = {'a': '\u00e2', 'e': '\u00ea', 'i': '\u00ee', 'o': '\u00f4', 'u': '\u00fb',
        'A': '\u00c2', 'E': '\u00ca', 'I': '\u00ce', 'O': '\u00d4', 'U': '\u00db'}


def surcharge(t):
    """Le fac-simile note la surcharge par \\sur{signo}{litero} — la dactylo
    frappait l'accent PAR-DESSUS la voyelle, faute de touche accentuee. Ce
    balisage n'a rien a faire dans l'edition de lecture, ou la lettre accentuee
    existe : « \\sur{\\textasciicircum{}}{a} » se lit « \u00e2 »."""
    def _un(m):
        return _SUR.get(m.group(1), m.group(1))
    return re.sub(r'\\sur\{\\textasciicircum\{\}\}\{([A-Za-z])\}', _un, t)


def orfa_parentezo(t):
    """Retire la parenthese fermante orpheline en fin de definition.

    L'original en compte trente : l'ouvrante a ete perdue a la frappe, ou bien
    consommee par l'extraction du domaine. Fermer ce qui n'a jamais ete ouvert
    n'apporte rien. On ne touche QUE la derniere, et seulement si le compte des
    autres est equilibre — sinon on ignore ou serait la faute.
    """
    if not t.endswith(')'):
        return t
    p = 0
    for c in t[:-1]:
        if c == '(':
            p += 1
        elif c == ')':
            p = max(0, p - 1)
    return _kupar(t[:-1]) if p == 0 else t


def fermi_kvalifikilon(t):
    """Ferme le qualificatif de tete dont la parenthese est restee ouverte.

    « transmisar. ... II. (biol. Igar pasar a la decendanti. » — la fermante
    manque apres l'abreviation, et le livre l'ecrit « (biol.) » des centaines
    de fois : sa place ne fait aucun doute.

    Cette regle doit passer AVANT fermi_parentezon, qui fermerait au BOUT du
    sens : « (biol. Igar pasar a la decendanti) », ou le domaine avale toute la
    definition. C'est le meme signe, pose a deux places, et une seule est
    juste.
    """
    m = RE_KVAL_MANKA.match(t)
    if m and t.count('(') > t.count(')'):
        resto = t[m.end():]
        if resto[:1] and not resto[:1].isspace():
            resto = ' ' + resto
        return '(%s)%s' % (m.group(1), resto)
    return t


def fermi_parentezon(t):
    """Ferme la parenthese restee ouverte en fin de definition.

    Le pendant exact d'orfa_parentezo. La fermante s'est perdue a la frappe et
    le sens s'acheve au milieu d'une incise — « ... (anke metaf », « ...
    (aludante penso, cienco, e c. », « ... (Ex. : la fragmento obskura ». Le
    livre en compte soixante-cinq. Laissee ouverte, la parenthese pend dans les
    deux editions, et la regle qui reconnait le domaine de tete s'y egare.

    On ne ferme QUE si la derniere ouvrante n'a aucune fermante apres elle et
    si tout ce qui la precede est equilibre. Ailleurs — chez « arachar », ou
    c'est la PREMIERE parenthese qui est restee ouverte — on ignore ou serait
    la faute, et fermer au bout deplacerait l'incise au lieu de la reparer.
    """
    i = t.rfind('(')
    if i < 0 or t.rfind(')') > i:
        return t
    av = t[:i]
    if av.count('(') != av.count(')'):
        return t
    return t.rstrip() + ')'


# « (anke metaf) » : le point de l'abreviation s'est perdu avec la parenthese
# fermante, en bout de ligne. Le livre ecrit « (anke metaf.) » cinquante fois
# contre dix-huit sans point — la forme n'est pas douteuse.
RE_ABREVO = re.compile(r'\((anke\s+metaf)\)', re.I)


def pointi_abrevo(t):
    """Rend son point a l'abreviation que la coupure de ligne a ecourtee."""
    return RE_ABREVO.sub(lambda m: '(%s.)' % m.group(1), t)


# Un qualificatif de tete dont la fermante s'est perdue : « (trans. Kustumigar
# animalo... », « (anat. Saliajo mi-sferatra... ». Le livre ferme celle-la des
# centaines de fois ; sa place ne fait aucun doute, juste apres l'abreviation.
#
# L'espace a pu tomber avec elle : « (bot.Frukto kapsula... » chez « folikulo ».
# Une CAPITALE collee au point de l'abreviation ouvre la definition ; elle ne
# continue pas le mot abrege. Sans cela la parenthese se fermait au bout du
# sens, et le domaine avalait toute la definition.
RE_KVAL_MANKA = re.compile(r'^\(([A-Za-zÀ-ÿ][A-Za-zà-ÿ]{1,11}\.)(?=\s|[A-ZÀ-Ý])')


def ekvilibrigi_parentezojn(t):
    """Retire les parentheses orphelines, faute de savoir ou serait leur paire.

    Le tapuscrit en laisse cinquante-cinq : « Gumo ek arboro) di India »,
    « Deprenar (per violento, koakto, de ulu to quon lu retenas. » Le
    fac-simile ne les rendra pas — l'original ne les a pas non plus. Il faut
    donc trancher, et la regle est celle qu'orfa_parentezo posait deja pour la
    fermante de fin : ON RETIRE LE SIGNE ORPHELIN. Le retirer ne fabrique aucun
    groupement que l'auteur n'a pas fait ; en inventer un le ferait.

    Deux exceptions, ou la place du conjoint ne fait aucun doute :

      * le qualificatif de tete — « (trans. » se ferme apres l'abreviation ;
      * la locution entre parentheses — « (arko inflexita : ... » chez
        « inflexar », que la page tronquee n'a jamais close. Elle ouvre une
        sous-entree ; oter sa parenthese la ferait disparaitre. On laisse alors
        le sens tel quel, desequilibre mais entier.
    """
    m = RE_KVAL_MANKA.match(t)
    if m and t.count('(') > t.count(')'):
        t = '(%s)%s' % (m.group(1), t[m.end():])
    pile = []
    orfaj = set()
    for i, c in enumerate(t):
        if c == '(':
            pile.append(i)
        elif c == ')':
            if pile:
                pile.pop()
            else:
                orfaj.add(i)
    if any(RE_LOKUCO_KRAMPA.match(t, i) for i in pile):
        return t
    orfaj.update(pile)
    if not orfaj:
        return t
    return _kupar("".join(c for i, c in enumerate(t) if i not in orfaj))


def netigar_punktuo(t):
    """Les scories de frappe : virgule doublee, point double, virgule-point.

    La dactylo a parfois frappe deux fois. Onze articles portent un point
    double — « ...e tonizala. . – DEFIS » chez « arniko », « (trans. .) » chez
    « reklamacar » —, quatre une virgule doublee, un une virgule suivie d'un
    point. Le fac-simile les garde ; l'edition de lecture, non.

    Le point double n'est retire que SEPARE d'une espace. Colles, « ie.. » et
    « venenifanta.. » sont deux cas contraires — une ellipse ecourtee et un
    point de trop — que rien ne distingue mecaniquement : ils sont traites un a
    un dans vorti.txt. Et l'ellipse de l'auteur, « ... », reste intacte.
    """
    t = re.sub(r',\s*,', ',', t)
    t = re.sub(r',\s*\.(?!\.)', ', ', t)
    # Le point separe de sa virgule : « fuzebla ye 201° C. , kontenata en la
    # kortico » chez salicino — le point est celui de l'abreviation, la virgule
    # celle de la phrase, et l'espace entre les deux n'est de personne.
    t = re.sub(r'\.\s+,', '.,', t)
    t = re.sub(r'(?<!\.)\.\s+\.(?!\.)', '.', t)
    return re.sub(r'  +', ' ', t)


# Les affixes que le livre donne comme VEDETTES, plus ceux que SUFIXI porte
# pour le rangement. SUFIXI seul ne suffit pas ici : bati pour oter UN suffixe
# d'un radical, il ignore « -im- », le suffixe de la fraction, qui est
# justement celui de « 1/10.000.000-ima ». Les affixes d'UNE lettre — « -e »,
# « -i » — n'y sont pas : ils se confondent avec les mots-outils.
AFIXI_KUN_FINALO = tuple(sorted(
    set(SUFIXI) | {'ab', 'ant', 'at', 'esm', 'im', 'int', 'ont', 'op', 'opl',
                   'ot', 'un'}, key=len, reverse=True))

RE_AFIXO_ESPACO = re.compile(
    r'(?<=[A-Za-z0-9\u00e0-\u00ff])-[\s\u00a0]+((?:%s)(?:o|a|e|i|ar|ir|or))'
    r'(?![A-Za-z\u00e0-\u00ff])' % '|'.join(AFIXI_KUN_FINALO))


def espacar(t):
    """Espacement de la ponctuation, usage franco-canadien.

    Isolee pour etre rejouable : la couche de relecture pose des chaines
    relevees AVANT la typographie, et les reposer telles quelles mangeait
    les espaces insecables — « familio«labiacei» ». On repasse donc ici
    apres elle. La fonction est idempotente.
    """
    t = re.sub(r',(?=[A-Za-zÀ-ÿ])', ', ', t)
    # Le tiret d'affixe ne se detache pas de son affixe : « 1/10.000.000- ima »
    # chez « metro » est « 1/10.000.000-ima », la dix-millionieme partie. C'est
    # la meme espace parasite que la vedette connait — « - as. » pour « -as »,
    # « bo - . » pour « bo- » —, posee cette fois dans le corps.
    # On exige un SUFFIXE suivi de sa desinence : sans quoi « radio- o
    # televizionorecevili » (megafono), ou le tiret reste en suspens devant la
    # conjonction, se recollait en « radio-o ». Les quatre autres tirets isoles
    # du livre — « ekirar- per », « perforuro- e », « implikas- kontre »,
    # « establisita- ube » — n'en sont pas davantage.
    t = RE_AFIXO_ESPACO.sub(r'-\1', t)
    # La parenthese fermante collee au mot suivant prend une espace — mais pas
    # celle qui fait CORPS avec le mot. L'auteur note ainsi l'element facultatif
    # : « leon(in)o » dit le lion et la lionne, « formac(es)o » la formation et
    # le fait de se former, « -(ant)ajo » le suffixe compose. Le mot continue
    # apres la parenthese, et l'espace le couperait en deux. On la reconnait au
    # tiret d'affixe qui la precede, ou a la lettre SEULE qui la suit — la
    # finale du mot. Trois cas dans le livre, et aucun faux frere : « F(z) esas
    # monodroma » porte deja son espace, « (aludante persono)Definuro » n'est
    # pas un element mais une incise.
    def _fermo_espaco(m):
        tiro, dedans, sekvo = m.group(1), m.group(2), m.group(3)
        korta = len(dedans) <= 6 and dedans.isalpha()
        if korta and (tiro or len(sekvo) == 1):
            return m.group(0)
        return '%s(%s) ' % (tiro, dedans)
    t = re.sub(r'(-?)\(([^()]*)\)(?=([A-Za-zÀ-ÿ]+))', _fermo_espaco, t)
    # « (olim).Vaporo-mashino » : le point qui suit la parenthese
    # fermante colle au mot suivant. 88 cas. On ne touche qu'apres une
    # parenthese : ailleurs, « CH3CO.CH3 » est une formule chimique.
    t = re.sub(r'\)\.(?=[A-ZÀ-Ý])', '). ', t)
    # Espace parasite CONTRE la parenthese : « ( fig.) » pour
    # « (fig.) », « hundo-herbo )» pour « hundo-herbo) ». La dactylo
    # espacait pour caler sa ligne. 15 ouvrantes et 33 fermantes.
    # « Igar(ulo) » : le mot colle a la parenthese ouvrante. Mais toutes ne se
    # detachent pas — « il(u) », « dea(la) », « a(ta) » notent une finale
    # facultative qui fait corps avec le mot, et « F(z) » est une fonction.
    # On separe donc seulement quand le contenu compte trois lettres ou plus,
    # ou porte autre chose que des lettres : c'est alors un complement ou un
    # domaine, non une desinence.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ])\((?=([^()]*)\))',
               lambda m: ' (' if (len(m.group(1)) >= 3
                                  or not m.group(1).isalpha()) else '(', t)
    # Ponctuation collee a une parenthese ouvrante : « Patrino homa.(Equivalanto
    # sentimentala... » chez matro. 30 cas. On epargne les formules : chez
    # stearino, « CH3.(CH2)16 » est une chaine carbonee, et l'espace y serait
    # fautive. Le signe distinctif d'une formule est le chiffre qui termine le
    # symbole precedent.
    def _pt(m):
        avan = t[:m.start()]
        if re.search(r'[A-Z][A-Za-z]?[0-9\u2080-\u2089]+$', avan):
            return m.group(0)
        return m.group(1) + ' ('
    t = re.sub(r'([.,;:!?])\(', _pt, t)
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\s+\)', ')', t)
    # Point orphelin apres la parenthese fermante — « (aludante la hari...) .
    # Di qua la koloro... ». Justifie, il ouvre un blanc dans la ligne.
    t = re.sub(r'\)\s+\.(?=\s|$)', ')', t)
    # Point superflu apres la parenthese de tete — « (komerco). Inter-egalesi ».
    # La parenthese ferme deja le qualificatif ; le point fait double emploi.
    t = re.sub(r'^(\([^()]{1,120}\))\s*\.+(?=\s|$)', r'\1', t)
    # Deux qualificatifs de suite — « (netrans.) (aludante vari). » chez
    # transitar : le point tombe apres le SECOND, et la regle ci-dessus ne
    # voyait que le premier.
    t = re.sub(r'^((?:\([^()]{1,80}\)\s*){2,})\.+(?=\s|$)', r'\1', t)
    # Deux-points superflu apres le qualificatif de tete — « (bruiso) : Poke
    # sonora ». La parenthese suffit ; le deux-points annoncerait une liste.
    t = re.sub(r'^(\([^()]{1,60}\))[\s\u00a0]*:[\s\u00a0]*', r'\1 ', t)
    # « e c » abrege « e cetere » : il prend le point. 325 occurrences le
    # perdaient, 455 l'avaient deja.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])e c(?![A-Za-zÀ-ÿ.])', 'e c.', t)
    # Espacement des ponctuations doubles, usage FRANCO-CANADIEN :
    # le point-virgule, le point d'exclamation et le point
    # d'interrogation ne prennent PAS d'espace devant — c'est la
    # difference d'avec l'usage de France, qui y met une espace fine.
    # Le deux-points, lui, en prend une, et elle est insecable pour
    # qu'il ne parte pas seul en tete de ligne. Idem dans les
    # chevrons. On recolle d'abord le deux-points a son mot suivant,
    # sinon la regle d'espace insecable le laisserait colle.
    t = re.sub(r':(?=[A-Za-zÀ-ÿ])', ': ', t)
    t = re.sub(r';(?=[A-Za-zÀ-ÿ])', '; ', t)
    t = re.sub(r'[\s\u00a0]*([;!?])', r'\1', t)
    t = re.sub(r'[\s\u00a0]*:', '\u00a0:', t)
    # Le chevron colle au mot voisin par le DEHORS : « familio«labiacei» ».
    # La regle suivante traite l'interieur ; celle-ci, l'exterieur.
    t = re.sub(r'(?<=[A-Za-zÀ-ÿ.,;:])(?=«)', ' ', t)
    t = re.sub(r'(?<=»)(?=[A-Za-zÀ-ÿ])', ' ', t)
    t = re.sub(r'«[\s\u00a0]*', '«\u00a0', t)
    t = re.sub(r'[\s\u00a0]*»', '\u00a0»', t)
    # Le numero de sens colle a son premier mot — « I.Tereno »,
    # « II.Alveolo ». On ne touche qu'aux chiffres romains : un point
    # suivi d'une majuscule est ailleurs une abreviation legitime.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])(I{1,3}|IV|VI{0,3}|IX|XI{0,2})\.'
    r'(?=[A-Za-zÀ-ÿ])', r'\1. ', t)
    # Ligne de bruit en fin de definition : la dactylo a barre une
    # ligne entiere a coups de guillemets et de tirets. Ce qui n'a
    # aucune lettre ni aucun chiffre ne dit rien.
    # _kupar plutot qu'un rstrip nu : l'ellipse finale qui marque le complement
    # regi — « ...kom valida ke... » — doit survivre au rognage du bruit.
    # La queue de bruit ne doit pas engloutir une ellipse suivie de sa
    # fermeture : « multa-... » compte six signes tous membres de la classe,
    # et y passait entierement. On l'epargne explicitement.
    t = re.sub(r'(?:[\s"\u00ab\u00bb\u2019\'.,;:_+*=/|\-\u2013\u2014]{6,})$',
               lambda m: m.group(0) if re.fullmatch(
                   r'[\s\u00a0-]*\.{2,}[\s\u00a0]*[\u00bb"\')\]]*', m.group(0)) else '', t)
    t = _kupar(t)
    return t


# Les points de suspension. La machine n'avait pas le caractere unique :
# l'auteur frappe trois points, parfois quatre. 96 occurrences.
#
# Quand une desinence ou un suffixe suit les points, il s'en detache par une
# espace et prend le tiret d'affixe. C'est la forme que le livre ecrit
# lui-meme chez « min » — « ne tam multe ...-a » — et chez « quadri- » —
# « Qua havas quar...-i » ; ailleurs le tiret, l'espace, ou les deux sont
# tombes : « quik...onta », « esar...ata », « t. e. ...is...inta ».
#
# Un MOT qui suit n'est pas un affixe et ne prend que l'espace : « lasas
# ...efikar », « preferar...kam », « lore...lore », « ...esante prezenta ».
# On s'en remet donc a la liste CLOSE des desinences, et au tiret que l'auteur
# a lui-meme frappe — « por...-eso » —, jamais a une ressemblance de forme :
# « esante » se decoupe en « es- » plus « -ante » sans etre pour autant un
# suffixe suivi d'une desinence.
#
# Les desinences d'UNE lettre — « -o », « -a », « -e », « -i » — n'y sont pas :
# ce sont aussi les mots-outils les plus courants du livre. « Esar prezenta
# ye... e regardar » (asistar), « domeno qua dependas de... e, konseque »
# (-i-) portent la conjonction, non la desinence. Ou l'auteur veut la
# desinence d'une lettre, il a frappe le tiret lui-meme : « ...-a » chez
# « min », « ...-i » chez « quadri- ».
DESINENCI = tuple(sorted(
    ('anta', 'inta', 'onta', 'ante', 'inte', 'onte', 'anto', 'into', 'onto',
     'ata', 'ita', 'ota', 'ate', 'ite', 'ote', 'ato', 'ito', 'oto',
     'ant', 'int', 'ont', 'ar', 'ir', 'or', 'as', 'is', 'os', 'us', 'ez'),
    key=len, reverse=True))

RE_ELIPSO = re.compile(
    r'\u2026[\s\u00a0]*(?:-\s*([A-Za-z\u00e0-\u00ff]+)|(%s))(?![a-z\u00e0-\u00ff])'
    % '|'.join(DESINENCI))


# Les composes que le livre ecrit tantot avec le trait d'union, tantot soudes.
# Il pose le trait a TOUS ses autres composes — « banko-komerco »,
# « natur-historio », « politiko-yuro », « milit-arto », « skerm-arto » — et a
# la grande majorite des emplois de ceux-ci ; on aligne les formes soudees qui
# restent hors du champ `fako`, ou la table des domaines s'en charge deja.
KOMPOZITA = (('yurocienco', 'yuro-cienco'),
             ('imprimarto', 'imprim-arto'))

RE_KOMPOZITA = tuple(
    (re.compile(r'(?<![-A-Za-z\u00e0-\u00ff])%s(?![A-Za-z\u00e0-\u00ff])' % a), b)
    for a, b in KOMPOZITA)


def kompozita(t):
    """Le compose soude rendu au trait d'union du livre."""
    for r, b in RE_KOMPOZITA:
        t = r.sub(b, t)
    return t


def elipso(t):
    """Trois ou quatre points rendus par le caractere unique, et l'affixe qui
    les suit detache par une espace et pointe d'un tiret."""
    t = re.sub(r'\.{3,}', '\u2026', t)
    t = RE_ELIPSO.sub(lambda m: '\u2026 -%s' % (m.group(1) or m.group(2)), t)
    # Le mot ordinaire qui suit ne prend que l'espace.
    t = re.sub(r'\u2026(?=[A-Za-z\u00c0-\u00ff])', '\u2026 ', t)
    return t


# La finale sous laquelle un mot se laisse citer : desinence nominale,
# adjectivale, adverbiale, verbale, ou participe.
RE_FINALO_CITITA = (r'(?:oj|o|a|e|i|ar|ir|or|as|is|os|us|ez'
                    r'|ant[aeio]|int[aeio]|ont[aeio]'
                    r'|at[aeio]|it[aeio]|ot[aeio])')


def steligar(ent):
    """La marque du mot non officiel, portee PARTOUT ou le mot est cite.

    Le livre declare ses mots non officiels a leur place alphabetique — la
    vedette porte l'asterisque — et les marque aussi quand il les cite dans une
    definition. Mais pas toujours : « werar » est marque cinquante fois et nu
    six fois, « publico » cinq fois et nu une fois, « grandoro » quatre fois et
    nu six fois. Le lecteur voyait le meme mot tantot signale, tantot non.

    On aligne sur la marque, et seulement pour les mots ou l'auteur l'a lui-meme
    posee au moins une fois : la ou il ne l'a jamais posee — « pondar »,
    « niuzo », « golfo », « tarda », « intrenar » —, l'ajouter serait une
    affirmation neuve, non une mise au net. Quatorze mots, 45 emplois.

    L'article du mot lui-meme est laisse tel quel : sa vedette porte deja la
    marque, et la redoubler dans sa propre definition n'apprend rien.
    """
    radiki={}
    for e in ent:
        v=e.get('vedetto') or ''
        if not v.startswith('*'): continue
        r=re.sub(r'(ar|ir|or|o|a|e|i)$', '', v[1:])
        if len(r)>=3: radiki[r]=v
    n=0
    for r,v in sorted(radiki.items()):
        marke=re.compile(r'\*(%s%s)(?![A-Za-zà-ÿ-])' % (re.escape(r), RE_FINALO_CITITA))
        if not any(marke.search(s) for e in ent for s in (e.get('senci') or [])):
            continue
        nuda=re.compile(r'(?<![*A-Za-zà-ÿ-])(%s%s)(?![A-Za-zà-ÿ-])'
                        % (re.escape(r), RE_FINALO_CITITA))
        for e in ent:
            if (e.get('vedetto') or '')==v: continue
            S=e.get('senci') or []
            for k,t in enumerate(S):
                u=nuda.sub(r'*\1', t)
                if u!=t: S[k]=u; n+=u.count('*')-t.count('*')
    return n


def typographio(ent):
    """Typographie de l'edition de lecture.

    Le fac-simile garde les tirets tels que la machine les a frappes — elle
    n'avait qu'une seule touche. L'edition de lecture, elle, peut les rendre.
    Trois regles, mesurees avant d'etre posees pour ne pas deborder sur les
    4 240 traits d'union internes, qui eux appartiennent aux mots :

      « elektro- -grandori »  -> « elektro-grandori »   (1 cas)
      « -- » ou « - » double  -> tiret cadratin         (20 cas)
      « mot - mot »           -> tiret demi-cadratin    (829 cas)
    """
    n=0
    # Les chevrons de la VEDETTE prennent leur espace, comme partout ailleurs
    # dans le livre. « "brokoli"-kaulo » est le seul cas ou ils restent DANS la
    # chaine : le mot ido n'y est cite qu'en partie, et le drapeau `citita`,
    # qui fait poser aux editions « \u00ab\u00a0amen\u00a0\u00bb », ne peut pas le porter.
    for e in ent:
        v=e.get('vedetto') or ''
        if '\u00ab' in v or '\u00bb' in v:
            u=re.sub(r'\u00ab[\s\u00a0]*', '\u00ab\u00a0',
                     re.sub(r'[\s\u00a0]*\u00bb', '\u00a0\u00bb', v))
            if u!=v: e['vedetto']=u; n+=1
    for e in ent:
        s=e.get('senci') or []
        for k,t in enumerate(s):
            o=t
            # Le tiret de separation colle a la parenthese du domaine :
            # « granda. -(cinemo) » chez « skreno », « direte.- (metaf.) » chez
            # « intuicar ». Le livre l'ecrit avec ses deux espaces quatre-vingt-
            # cinq fois ; treize fois l'une des deux manque. La parenthese d'un
            # AFFIXE n'en est pas une — « = -(at)ajo », « equivalas -(ant)ajo » :
            # la le mot continue apres la fermante, et le tiret lui appartient.
            t=re.sub(r'\s*-\s*(\([^()]*\))(?![A-Za-zà-ÿ])', r' - \1', t)
            t=re.sub(r'(\w)- -(\w)', r'\1-\2', t)          # trait redouble d'une coupure
            t=re.sub(r'(?<![-\w])(?:- -|--)(?![-\w])', '—', t)
            t=re.sub(r'(?<=\S) - (?=\S)', ' – ', t)
            # Le « + » du tapuscrit marque les mots non officiels ; la
            # tradition ido ecrit une asterisque. 214 occurrences.
            # Un mot non officiel est un mot ido, donc en minuscule : « +H₂O »,
            # dans la formule de la morphine, est le plus de la chimie et non
            # la marque de l'auteur.
            #
            # La marque est COLLEE au mot qu'elle marque — la dactylo ne laissait
            # pas d'espace : « pri+grandoro », « sur+stencilo », « vazo+kluza »,
            # « o+sesiono ». Le livre donne bien « *grandoro », « *stencilo »,
            # « *kluza », « *sesiono » comme vedettes non officielles.
            t=re.sub(r'\+(?=[a-zà-ÿ])', '*', t)
            # Detachee du mot, elle ne l'est que si elle OUVRE le fragment ou
            # suit une parenthese ouvrante : « legi (+ leyi) » chez « cienco ».
            # Entre deux termes, c'est le plus de l'algebre, que la regle
            # precedente prenait pour la marque : « ax² + bx + c = 0 » chez
            # « diskriminanto », « a + b i e a' + b' i » chez « konjugar »,
            # « a² = b² + c » chez « pitagorala » — quatre asterisques posees
            # sur des inconnues.
            t=re.sub(r'(?:^|(?<=[(\[«“"]))\+\s+(?=[a-zà-ÿ])', '*', t)
            # Guillemets : la machine n'avait que la double apostrophe droite.
            # On ne convertit que les PAIRES — 834 sur 1 690 apostrophes ; les
            # orphelines restent droites plutot que d'ouvrir un chevron qui ne
            # se refermerait jamais.
            t=re.sub(r'"([^"]{1,120})"', r'«\1»', t)
            # Espaces manquantes apres la ponctuation : la dactylo serrait pour
            # tenir la ligne. 258 virgules et 136 parentheses fermantes.
            # cifri() et formuli() ne sont PAS ici : ce sont des transformations
            # de rendu, et la couche de relecture cherche des chaines relevees
            # sur le texte brut. « H2 Hg3 Si4 O12 » ne se retrouve plus une fois
            # les indices poses ; on les pose donc APRES elle.
            t=pointi_sencoj(surcharge(espacar(netigar_punktuo(t))))
            if t!=o: s[k]=t; n+=1
    return n

def corriger_vedettes(ent, fichier=f"{T}/vedetti.txt"):
    """Corrections de vedettes, relevees a l'oeil.

    La couche des jugements ne touche que les definitions : une vedette est un
    article, pas une occurrence, et la corriger par regle a deja mal tourne.
    Elle se corrige donc a la main, une ligne par cas, avec le motif ecrit en
    regard. Le fac-simile, lui, garde la graphie de l'original.
    """
    if not os.path.exists(fichier): return 0
    corr={}
    for l in open(fichier,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        p=l.split("\t")
        if len(p)>=2 and p[0].strip() and p[1].strip(): corr[p[0].strip()]=p[1].strip()
    n=0
    for e in ent:
        v=e.get('vedetto')
        # Cible precise : « tri@600:23 » ne touche que l'article de la page 600
        # ligne 23. Le livre porte DEUX « tri » — le chiffre 3 et le prefixe —
        # et seul le second prend le trait d'union.
        c = corr.get("%s@%d:%d" % (v, e['image'], e['ligno']))
        if c is None: c = corr.get(v)
        if c is not None: e['vedetto']=c; n+=1
    return n

def corriger_vorti(ent, fichier=f"{T}/vorti.txt"):
    """Corrections de mots dans les definitions, relevees a l'oeil.

    Le pendant de vedetti.txt pour le corps des articles. Deux passes
    automatiques ont deja ete rejetees ici — la frequence donnait « papuli »
    pour « populi », la racine « falko » pour « talko » — parce qu'un
    dictionnaire de dix mille racines n'est pas tout le lexique de la langue.
    On ecrit donc les cas un par un, avec leur motif.
    """
    if not os.path.exists(fichier): return 0
    corr={}
    for l in open(fichier,encoding='utf-8'):
        l=l.rstrip("\n")
        if not l.strip() or l.startswith("#"): continue
        p=l.split("\t")
        if len(p)>=2 and p[0].strip() and p[1].strip(): corr[p[0].strip()]=p[1].strip()
    if not corr: return 0
    # Une correction peut porter sur PLUSIEURS mots — « en decen danto » pour
    # « en decendanto », « ii aDom » pour « di mikra » : la machine a coupe ou
    # soude la ou il ne fallait pas, et le mot fautif n'a pas de frontiere
    # propre. On accepte donc une suite de mots a gauche comme a droite.
    mo=re.compile(r"(?<![A-Za-zÀ-ÿ-])(%s)(?![A-Za-zÀ-ÿ-])"
                  % "|".join(re.escape(k).replace(r"\ ", r"\s+")
                             for k in sorted(corr, key=len, reverse=True)))
    n=0
    for e in ent:
        s=e.get('senci') or []
        for k,t in enumerate(s):
            nt,c = mo.subn(lambda m: corr[re.sub(r"\s+"," ",m.group(1))], t)
            if c: s[k]=nt; n+=c
    return n

def appliquer_jugements(ent):
    import glob
    total=0
    for fic, rep in JUGEMENTS:
        if not os.path.exists(fic): continue
        fiches={x['id']:x for x in json.load(open(fic))}
        for f in sorted(glob.glob(f"{rep}/*.txt")):
            for l in open(f,encoding='utf-8'):
                i,_,v = l.rstrip("\n").partition("\t")
                if not v.strip() or not i.strip().isdigit(): continue
                x=fiches.get(int(i))
                if x is None: continue
                mot, bon = x['mot'], v.strip()
                # Deux motifs, essayes dans l'ordre. Le premier recolle une
                # cesure — « pro-duktita » -> « produktita ». Il ne doit pas
                # etre le seul : « uaze » corrige en « quaze » n'est pas une
                # cesure mais une lettre tombee, et le motif de cesure y
                # cherchait « q-uaze » sans rien trouver, en silence.
                motifs=[]
                if bon.lower().endswith(mot.lower()) and len(bon)>len(mot):
                    tete=bon[:len(bon)-len(mot)]
                    motifs.append(re.compile(r'\b'+re.escape(tete)+r'[-\s]+'+re.escape(mot)+r'\b', re.I))
                motifs.append(re.compile(r'\b'+re.escape(mot)+r'\b', re.I))
                for mo in motifs:
                    pose=0
                    for e in ent:
                        s=e.get('senci') or []
                        for k,t in enumerate(s):
                            nt,n=mo.subn(bon, t)
                            if n: s[k]=nt; pose+=n
                    total+=pose
                    if pose: break
    return total

if __name__=="__main__":
    ent=konstrui()
    os.makedirs(f"{T}/edicioni", exist_ok=True)
    with open(f"{T}/edicioni/dicionario.jsonl","w",encoding='utf-8') as f:
        for e in ent:
            f.write(json.dumps({k:v for k,v in e.items() if k!='lineoj'}, ensure_ascii=False)+"\n")
    print(f"{len(ent)} enregistrements")
    c=collections.Counter(d for e in ent for d in e['drapeli'])
    print("drapeaux :", c.most_common())
    print("sans aucun drapeau :", sum(1 for e in ent if not e['drapeli']))
    print("avec fako :", sum(1 for e in ent if e['fako']),
          "| avec nom latin :", sum(1 for e in ent if e['latina']),
          "| plusieurs sens :", sum(1 for e in ent if len(e['senci'])>1))
