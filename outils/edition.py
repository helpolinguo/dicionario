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
import numpy as np, os, pickle, re, collections, sys, json, os
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
# Le nom scientifique ne finit pas toujours sur un tiret ou en fin de segment :
# il est souvent suivi d'une parenthese fermante — « (L. triticum caninum) » —
# d'une virgule qui reprend la phrase, ou du numero du sens suivant —
# « L. aquila II. ». Ancre sur le seul tiret, il restait dans la definition de
# soixante-sept articles. On borne donc le nom par sa FORME — quatre mots
# latins au plus, plus une seconde forme apres virgule pour « anas, anatis » —
# au lieu de le borner par ce qui le suit.
RE_LATINA = re.compile(
    r'(?:[-–.(,;:]|^)\s*L\.\s*'
    r'([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,3}'
    r'(?:\s*,\s*[A-Za-z][A-Za-z-]*)?)'
    r'\s*(?=[-–)(:;,]|\.\s|\.?$|\s(?:I{1,3}|IV|V|VI)\.)')
# Les sens se separent par « - II. », mais le tiret manque souvent : « ...
# komenco-punto e fino-parto. II. (gram.) ... ». On coupe donc aussi sur un
# point suivi du numero de sens, ce qui vaut pour 107 articles.
# Six articles numerotent leurs sens en chiffres ARABES — « grapino »,
# « kapelo », « koliaro », « kondamnar », « konfliktar » — et « iambo » melange
# les deux niveaux. Sans cette branche, tout leur contenu restait dans un seul
# sens. On exige la majuscule ou la parenthese apres le numero, ce qui ecarte
# « 1.000 » et les formules chimiques. Le « l » lu pour « 1 » est admis : la
# confusion est constante dans ce tapuscrit.
RE_SENCO  = re.compile(r'\s*(?:[-–]\s*|(?<=\.)\s*)'
                       r'(?=(?:I{1,3}|IV|V|VI)[.,]\s?|[l\d]\d?\.\s*[A-ZÀ-Ý(])')
FINALES_OK = ("o","a","e","i","ar","ir","or")

def charger_texte():
    from decoder import charger, page_texte
    from generer import exceptions
    lab,M=charger(); tab=np.load(f"{T}/cls_lab.npy",allow_pickle=True); exc=exceptions()
    corrigees=set((p,k,c) for (p,k,c) in exc)
    pages={}
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
        pages[pg]=out
    return pages, corrigees


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

def decouper(pages, corrigees):
    ent=[]
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
        RE_VED=re.compile(r'^\.?[+-]?\s?[A-Za-z][A-Za-z\'’"-]{0,30}\s?-?\s?\.')
        # La ligne blanche ne se lit pas dans le texte : elle N'EST PAS dans la
        # grille. page_texte() ne rend que les lignes detectees, et leurs
        # numeros sautent — 2, 3, puis 5. C'est ce SAUT qui marque le blanc.
        # A chercher une chaine vide, la regle ne se declenchait que sur la
        # premiere ligne de chaque page : la 536 ne rendait qu'un article sur
        # quatorze, et « simpla », « utila », « granda » manquaient au livre.
        prec=None; ved2=set()
        for k,s in pages[pg]:
            if not s.strip(): continue
            blanc = (prec is None) or (k - prec > 1)
            if blanc and RE_VED.match(s.lstrip()): ved2.add(k)
            prec=k
        cur=None
        for k,s in pages[pg]:
            if not s.strip(): continue
            if k in ved or k in ved2:
                if cur: ent.append(cur)
                cur=dict(image=pg, pagino=pg-DECALAGE_FOLIO, ligno=k, lineoj=[(k,s)])
            elif cur is not None:
                cur['lineoj'].append((k,s))
        if cur: ent.append(cur)
    for e in ent:
        e['korektita'] = sum(1 for (k,_) in e['lineoj']
                             for c in range(120) if (e['image'],k,c) in corrigees)
    return ent

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
                       r'(?=[+*]?[a-zà-ÿ][a-zà-ÿ\'\u2019-]{1,25}\s*[:.!]\s)')

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
                if len(t)-m.end() < 25: continue
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

def analizar(e, lexique=None):
    t=e.get('teksto_brut')
    if t is None:
        t=recoller([s for _,s in e['lineoj']], lexique)
    t=re.sub(r'\s+',' ',t).strip()
    for a,b in _texti().items():
        if a in t: t=t.replace(a,b)
    # Le fac-simile garde l'espace que la dactylo a laissee autour du tiret
    # d'affixe ; l'edition de lecture recolle. « - as. » est « -as », « - at
    # - . » est « -at- », « bo - . » est « bo- ». Sans quoi la vedette etait
    # vide et l'article introuvable.
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
    e['teksto']=t
    # Le tapuscrit marque les mots non officiels d'un « + » en exposant ; la
    # tradition ido ecrit une asterisque. On la restitue ici — le fac-simile,
    # lui, garde le signe frappe.
    # La vedette peut etre entre guillemets — « "alpari" », « "amen" » — ou
    # precedee d'un point parasite. On les admet, puis on les retire du mot.
    t = t.lstrip('. ')
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
    resto = re.sub(r'[\s.\-—–]+$', '', resto)
    e['lingui']=[]; e['kodo']=None
    me = RE_EPELE.search(resto)
    if me:
        noms=[EPELE.get(x.strip(' .')) for x in me.group(1).split(',')]
        if all(noms):
            e['lingui']=noms; e['kodo']=me.group(1).strip()
            resto = resto[:me.start()].rstrip(' -–.')
    # Le code n'est pas toujours precede d'un tiret. Il se colle au point
    # (« agar lo.DEFIS. »), a la parenthese fermante (« (anke metaf.)DEFIRS »),
    # mais aussi a une parenthese OUVRANTE restee ouverte (« ...alambiko.
    # (DEFIRS »), a une virgule (« ...deliberita, DEFIS ») ou a rien du tout
    # (« ...kavalrio DEFIRS »). Vingt-et-un articles gardaient ainsi leur code
    # au milieu de la definition et passaient pour « sen-lingua ». La casse
    # protege : _lire_code exige un jeton majoritairement haut de casse, et le
    # dernier mot d'une definition ne l'est jamais.
    mj = None if e['kodo'] else re.search(r'(?:[-–.,()*]|\s|^)\s*([A-Za-z]{1,12})$', resto)
    if mj:
        li=_lire_code(mj.group(1))
        if li:
            e['lingui']=li; e['kodo']=mj.group(1)
            resto = resto[:mj.start()].rstrip(' -–.')
    resto = resto.lstrip(' -–.,;:')
    # « ed. (Videz "e"). » : la parenthese porte un RENVOI, pas un domaine. Prise
    # pour un domaine, elle laissait l'article sans definition du tout.
    mf=None if re.match(r'^\(\s*(?:Videz|videz|Vid\.)\b', resto) else (
        RE_FAKO.match(resto) or RE_FAKO2.match(resto))
    e['fako']= mf.group(1).rstrip('.').strip() if mf else None
    if mf: resto = resto[mf.end():]
    # Deux parentheses de suite : la seconde precise la premiere et non le
    # sens. « pensar. (trans. e netrans.) (ulo, ad ulo, pri ulu od ulo) » —
    # le regime appartient au marqueur de transitivite, pas a la definition,
    # qui commencait donc par une parenthese orpheline.
    if e['fako']:
        m2 = re.match(r'^[\s.,;:\u2013-]*\(([^()]{1,40})\)\s*\.?\s*(?=[-\u2013]?\s*(?:[IVX]{1,3}\.|[A-Z\u00c0-\u00dd]))', resto)
        if m2:
            e['fako'] = "%s) (%s" % (e['fako'], m2.group(1).rstrip('.').strip())
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
    senci=[s.strip(' -–.,;:') for s in RE_SENCO.split(resto) if s.strip(' -–.,;:')]
    e['senci']= senci if senci else ([resto] if resto else [])
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
    elif not any(v.lower().endswith(f) for f in FINALES_OK): e['drapeli'].append('finalo-nekustumala')
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

def konstrui():
    pages,corr = charger_texte()
    brut=decouper(pages,corr)
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
    n=corriger_vorti(ent)
    if n: print("mots corriges dans les definitions : %d"%n)
    import relire as _rel
    n,r=_rel.appliquer(ent)
    if n or r: print("relecture des definitions : %d corrections posees, %d refusees"%(n,r))
    # La relecture pose des chaines relevees avant la typographie : on repasse
    # l'espacement derriere elle. espacar() est idempotente.
    for e in ent:
        S=e.get('senci') or []
        for k,t in enumerate(S): S[k]=cifri(espacar(t))
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
    RE_NUM=re.compile(r'^(?:(?:I{1,3}|IV|VI{0,3}|IX|X|[l\d]\d?)[.)](?!\d)\s*'
                      r'|(?:I{1,3}|IV|VI{0,3}|IX|X),\s*(?=[A-ZÀ-Ý(]))')
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
            S.append(u)
        fus=[]
        for i,t in enumerate(S):
            if RE_ETIQ.match(t) and i+1 < len(S):
                S[i+1] = t.rstrip('.') + ' ' + S[i+1]
                continue
            if t: fus.append(t)
        e['senci']=fus
    if n_num: print("numeros de sens retires : %d"%n_num)
    v=[e['vedetto'].lower() for e in ent]
    for i in range(1,len(v)):
        if v[i] and v[i-1] and v[i] < v[i-1]:
            ent[i]['drapeli'].append('ordino-ruptita')
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
    # « lOOOmetri » : la dactylo a soude le nombre a son unite. On exige trois
    # chiffres et trois minuscules, ce qui epargne les formules — « C6H4 » n'a
    # qu'une lettre, et elle est capitale.
    t = re.sub(r'(?<![A-Za-zÀ-ÿ])(\d{3,})(?=[a-zà-ÿ]{3,})', r'\1 ', t)
    return t


def espacar(t):
    """Espacement de la ponctuation, usage franco-canadien.

    Isolee pour etre rejouable : la couche de relecture pose des chaines
    relevees AVANT la typographie, et les reposer telles quelles mangeait
    les espaces insecables — « familio«labiacei» ». On repasse donc ici
    apres elle. La fonction est idempotente.
    """
    t = re.sub(r',(?=[A-Za-zÀ-ÿ])', ', ', t)
    t = re.sub(r'\)(?=[A-Za-zÀ-ÿ])', ') ', t)
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
    t = re.sub(r'\(\s+', '(', t)
    t = re.sub(r'\s+\)', ')', t)
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
    t = re.sub(r'(?:[\s"\u00ab\u00bb\u2019\'.,;:_+*=/|\-\u2013\u2014]{6,})$', '', t).rstrip(' .,;:-\u2013\u2014')
    return t


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
    for e in ent:
        s=e.get('senci') or []
        for k,t in enumerate(s):
            o=t
            t=re.sub(r'(\w)- -(\w)', r'\1-\2', t)          # trait redouble d'une coupure
            t=re.sub(r'(?<![-\w])(?:- -|--)(?![-\w])', '—', t)
            t=re.sub(r'(?<=\S) - (?=\S)', ' – ', t)
            # Le « + » du tapuscrit marque les mots non officiels ; la
            # tradition ido ecrit une asterisque. 214 occurrences.
            t=re.sub(r'\+(?=[A-Za-zÀ-ÿ])', '*', t)
            # Guillemets : la machine n'avait que la double apostrophe droite.
            # On ne convertit que les PAIRES — 834 sur 1 690 apostrophes ; les
            # orphelines restent droites plutot que d'ouvrir un chevron qui ne
            # se refermerait jamais.
            t=re.sub(r'"([^"]{1,120})"', r'«\1»', t)
            # Espaces manquantes apres la ponctuation : la dactylo serrait pour
            # tenir la ligne. 258 virgules et 136 parentheses fermantes.
            t=cifri(espacar(t))
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
