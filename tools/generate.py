"""Generation des fichiers de contenu LaTeX, une ligne de source par ligne du livre."""
import numpy as np, os, pickle, sys
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"; RAC="/root/dicionario"


# --- assiette des pages, en millimetres ---------------------------------
PASH_MM = 2.540          # pas de la machine : un dixieme de pouce
PASV_MM = 4.321          # interligne mesure
LARG_MM, HAUT_MM = 210.0, 297.0
ORIGX_MM, ORIGY_MM = 21.9, 12.44      # origine de la zone de texte composee
# Le bloc de texte est pose au meme endroit sur toutes les pages de meme main.
# La ligne la plus longue du livre fait 190,5 mm sur une feuille de 210 : il
# reste 19,5 mm de marges, que l'on partage en donnant plus au cote de la
# couture, ou l'ouvrage — 639 pages — perd de la place a la reliure.
# Le bloc est cale sur la TRANCHE, et non sur la couture.
#
# Il l'etait sur la couture jusqu'ici : marge gauche fixe, bord droit libre.
# Les marges gauches etaient donc parfaitement regulieres — 13,5 mm au recto,
# 8,0 mm au verso — mais les marges droites allaient de 6 a 72 millimetres,
# puisque le bord droit suivait la ligne la plus longue de la page. A
# l'ouverture, deux pages en regard n'avaient aucun bord commun.
#
# On cale desormais sur le cote exterieur : le verso par sa gauche, le recto
# par sa droite. La marge de tranche est alors la meme partout, et tout le
# jeu des longueurs de ligne se reporte du cote de la couture — ou il est le
# bienvenu, un ouvrage de 640 pages perdant beaucoup de place a la reliure.
BORD_EXT  = 8.0          # marge exterieure (tranche) : la meme des deux mains
GOUTTIERE_MIN = 12.0     # jamais moins, du cote de la couture
BORD_HAUT = 11.0         # marge de tete, la meme partout
MARGE_BAS_MIN = 6.0
MARGE_EXTREME = 3.0      # butee absolue pour les pages hors norme

ECHAP={'\\':r'\textbackslash{}', '{':r'\{', '}':r'\}', '%':r'\%', '#':r'\#',
       '_':r'\_', '&':r'\&', '$':r'\$', '^':r'\textasciicircum{}',
       '~':r'\textasciitilde{}', '"':r'\textquotedbl{}', "'":r'\textquotesingle{}',
       '<':r'\textless{}', '>':r'\textgreater{}', '|':r'\textbar{}'}
def esc(cellules):
    """Echappe une SUITE de contenus de cellules. Un contenu de plus d'un
    caractere commencant par une contre-oblique est du LaTeX brut (surfrappe,
    caractere compose) et passe tel quel."""
    out=[]
    for c in cellules:
        out.append(c if (len(c)>1 and c.startswith("\\")) else ECHAP.get(c,c))
    return "".join(out)

_EXC=None
def exceptions():
    """Table (page, ligne, colonne) -> lecture retenue.

    Deux fichiers : `exceptions.txt`, ecrit par les correcteurs automatiques,
    et `exceptions_manuel.txt`, arbitre a l'oeil. Le second l'emporte toujours
    et n'est jamais reecrit par un programme.
    """
    global _EXC
    if _EXC is None:
        _EXC={}
        for nom in ("exceptions_fins.txt","exceptions_ornements.txt","exceptions_paires.txt","exceptions.txt","exceptions_relecture.txt","exceptions_manuel.txt"):
            p=os.path.join(T, nom)
            if not os.path.exists(p): continue
            for l in open(p, encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,c,v=l.split("\t")
                _EXC[(int(a),int(b),int(c))]=v
    return _EXC


_SOU=None
_DEBUTS=None
def debuts_rendus():
    """Premieres lettres rendues par restore_starts.py, par page."""
    global _DEBUTS
    if _DEBUTS is None:
        p=os.path.join(T,"debuts.pkl")
        _DEBUTS=pickle.load(open(p,"rb")) if os.path.exists(p) else {}
    return _DEBUTS

_FILETS=None
def filets_neufs():
    """Filets recalcules par redo_rules.py, par page."""
    global _FILETS
    if _FILETS is None:
        p=os.path.join(T,"filets.pkl")
        _FILETS=pickle.load(open(p,"rb")) if os.path.exists(p) else {}
    return _FILETS

def sou_relus():
    """Plages de soulignement relevees a l'oeil, par (page, ligne).

    Elles remplacent entierement les plages detectees : le relecteur a vu la
    page, la detection ne fait que mesurer un filet dont elle situe mal la
    ligne de base.
    """
    global _SOU
    if _SOU is None:
        _SOU={}
        p=os.path.join(T,"sou_relus.txt")
        if os.path.exists(p):
            for l in open(p, encoding='utf-8'):
                l=l.rstrip("\n")
                if not l.strip() or l.startswith("#"): continue
                a,b,c=l.split("\t")
                _SOU[(int(a),int(b))]=[tuple(int(x) for x in seg.split("-"))
                                       for seg in c.split(",") if seg]
    return _SOU

def _ebarber(plage, cellules):
    """Ebarbe une plage de soulignement.

    Le filet est mesure au pixel pres, mais il lui arrive de deborder d'une ou
    deux cellules sur le mot suivant. Un filet ne souligne pas une lettre isolee
    a son extremite : on retranche donc les groupes de une ou deux cellules
    separes du corps de la plage par une espace. Les espaces interieures, elles,
    sont conservees — le tapuscrit souligne bien « historio di Italia » d'un
    seul trait. Un filet isole d'une ou deux cellules est du bruit.
    """
    a, b = plage
    n=len(cellules)
    a=max(a,0); b=min(b,n-1)
    if b < a: return None
    grp=[]; i=a
    while i<=b:
        if cellules[i]!=" ":
            j=i
            while j+1<=b and cellules[j+1]!=" ": j+=1
            grp.append((i,j)); i=j+1
        else: i+=1
    if not grp: return None
    if len(grp)>1 and grp[-1][1]-grp[-1][0]+1 <= 2: grp=grp[:-1]
    if len(grp)>1 and grp[0][1]-grp[0][0]+1 <= 2: grp=grp[1:]
    if not grp: return None
    a2,b2 = grp[0][0], grp[-1][1]
    if b2-a2+1 <= 2 and len(grp)==1: return None
    return (a2,b2)

def lignes_page(pg, lab, M, tab):
    z=np.load(f"{T}/cellules/p-{pg:03d}.npz", allow_pickle=True)
    lg=z['lignes']; ncol=z['occ'].shape[1]
    sou=pickle.loads(z['sou'].item()) if 'sou' in z else {}
    # Filets recalcules : voir tools/redo_rules.py. La detection d'origine
    # prenait les empattements superieurs alignes des capitales de DEFIRS pour
    # un soulignement, et les rapportait a la ligne du dessus. On ne reecrit pas
    # le corpus de cellules pour autant — 295 Mo, et un accident de format y a
    # deja coute 144 pages : la correction est une couche par-dessus.
    neufs=filets_neufs().get(pg)
    if neufs: sou=neufs
    from decode import bavures
    sel=np.where(M[:,0]==pg)[0]
    bv=bavures()[sel]
    par={}
    for (p,k,c),b,x in zip(M[sel], lab[sel], bv):
        par.setdefault(int(k),{})[int(c)]=" " if x else tab[b]
    # Debuts de ligne rendus (voir tools/restore_starts.py). Ils tombent AVANT
    # la colonne zero : on decale la PAGE ENTIERE d'autant de cellules qu'il en
    # manque. Decaler la seule ligne concernee la poserait une cellule a droite
    # de sa place reelle ; en decalant tout, les positions relatives sont
    # conservees au caractere pres, et le bloc, dont la marge est fixee
    # ailleurs, retombe au meme endroit sur la feuille.
    #
    # Le decalage s'applique AVANT les exceptions : celles-ci sont relevees a
    # l'oeil sur le fac-simile decale, donc deja dans la nouvelle numerotation.
    deb=debuts_rendus().get(pg)
    dec=0
    if deb:
        dec=-min(c for d0 in deb.values() for c in d0)
        par={k:{c+dec:v for c,v in d0.items()} for k,d0 in par.items()}
        sou={k:(yy,[(a+dec,b+dec) for a,b in pl],t) for k,(yy,pl,t) in sou.items()}
        ncol+=dec
        for k,d0 in deb.items():
            for c,ch in d0.items(): par.setdefault(int(k),{})[c+dec]=ch
    for (pp,kk,cc),v in exceptions().items():
        if pp==pg: par.setdefault(int(kk),{})[int(cc)]=v
    kmax=int(lg[:,0].max())
    # Une correction peut porter au-dela du bloc : ce sont les fins de ligne
    # que le decoupage avait coupees. On elargit la ligne pour les accueillir,
    # sans avoir a redecouper la page.
    for (pp,kk),d0 in list(par.items()) if False else []: pass
    for k,d0 in par.items():
        if d0: ncol=max(ncol, max(d0)+1)
    out=[]
    for k in range(kmax+1):
        d=par.get(k,{})
        s=[d.get(c," ") for c in range(ncol)]
        s=[(c if c not in ("", None) else " ") for c in s]
        plages=[]
        relu = sou_relus().get((pg,k))
        if relu is not None:
            # Releve a l'oeil : on prend tel quel, sans fusion ni ebarbage —
            # ces corrections-la visent justement a redresser ce que la mesure
            # automatique avait mal place.
            plages=[(a,b) for a,b in relu if b>=a]
        elif k in sou:
            yy,pl,tot=sou[k]
            plages=sorted((a,b) for a,b in pl if b>=a)
            # Le ruban saute : un filet interrompu sur une ou deux cellules
            # reste le meme filet. Deux plages separees de plus de deux
            # cellules, elles, sont bien deux soulignements distincts
            # (« cinocefalo » et « zool. » sont a trois cellules l'une de
            # l'autre).
            fus=[]
            for a,b in plages:
                if fus and a-fus[-1][1] <= 2: fus[-1]=(fus[-1][0], max(fus[-1][1],b))
                else: fus.append((a,b))
            plages=[p for p in (_ebarber(p, s) for p in fus) if p]
            # Deux regles reglees sur 1 698 lignes relevees a l'oeil :
            # un filet ne commence ni ne finit sur une case vide, et deux
            # troncons separes seulement par des cases pleines sont le meme
            # filet, interrompu par l'usure du ruban.
            f2=[]
            for a,b in plages:
                if f2 and a-f2[-1][1] <= 3 and all(
                        (c < len(s) and s[c] != " ") for c in range(f2[-1][1]+1, a)):
                    f2[-1]=(f2[-1][0], b)
                else: f2.append((a,b))
            # Troisieme regle : un filet ne commence pas au milieu d'un mot.
            # La detection produisait « ritato » sous « autoritato » et « as, »
            # sous « esas, ». Si le debut n'est pas a une frontiere de mot — une
            # espace, une parenthese ouvrante, un guillemet — on le ramene au
            # debut du mot ; et si le filet ne couvre pas au moins les trois
            # cinquiemes de ce mot, c'est du bruit et on le jette.
            # Le « + » qui marque les vedettes non officielles est un signe,
            # pas une lettre : le filet commence apres lui, sous la vedette.
            # Sans l'admettre comme frontiere, « +quoniam » perdait son
            # soulignement — le filet, pourtant bien mesure, etait juge
            # commencant au milieu d'un mot et jete.
            FRONT=set(' ("\'+')
            plages=[]
            for a,b in f2:
                while b > a and (b >= len(s) or s[b] == " "): b -= 1
                while a < b and (a >= len(s) or s[a] == " "): a += 1
                if b < a: continue
                # Un filet qui commence au milieu d'un mot est un fantome de
                # la mesure : on le jette. L'etendre au mot entier notait aussi
                # bien sur la verite terrain (84,5 % contre 83,9 % de lignes
                # exactes), mais c'est le mauvais echec — mieux vaut un
                # soulignement manquant qu'un mot souligne a tort, qui saute
                # aux yeux : « autoritato » et « esas, » l'ont montre.
                if not (a == 0 or (a-1 < len(s) and s[a-1] in FRONT)):
                    continue
                plages.append((a,b))
        out.append((k, s, plages))
    return out, ncol

def texifier(cells, plages):
    """Compose une ligne : espaces -> \\cel{n}, plages soulignees -> \\sou{...}."""
    n=len(cells)
    marque=[False]*n
    for a,b in plages:
        for j in range(max(a,0), min(b+1,n)): marque[j]=True
    # on tronque les espaces de fin
    fin=n
    while fin>0 and cells[fin-1]==" " and not marque[fin-1]: fin-=1
    if fin==0: return ""
    res=[]; i=0; vide=0
    while i<fin:
        if cells[i]==" " and not marque[i]:
            vide+=1; i+=1; continue
        if vide: res.append(f"\\cel{{{vide}}}"); vide=0
        if marque[i]:
            j=i
            while j<fin and marque[j]: j+=1
            res.append("\\sou{"+esc(cells[i:j])+"}")
            i=j
        else:
            j=i
            while j<fin and cells[j]!=" " and not marque[j]: j+=1
            # on garde les espaces simples internes en clair pour la lisibilite
            while j<fin and not marque[j] and (cells[j]!=" " or (j+1<fin and cells[j+1]!=" " and not marque[j+1])):
                j+=1
            res.append(esc(cells[i:j]))
            i=j
    return "".join(res)

_LP=None
def lignes_plus(fichier=f"{T}/lignes_plus.txt"):
    """Lignes qu'une RE-COUPE ulterieure de la page a laissees hors du bloc.

    Vingt-et-une pages ont ete decoupees par une version de bloc_texte() qui
    arretait le bloc trop haut ; leur .npz ne porte donc plus les dernieres
    lignes de la page, alors que le scan, lui, les porte. Ce fichier les rend,
    telles que le scan les donne, et il sert AUX DEUX editions : le fac-simile
    les recompose, l'edition de lecture les lit. Une seule source, donc pas de
    divergence possible.

    Une ligne du fichier : page<TAB>numero de ligne<TAB>texte de la grille.
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


def ecrire(pg, lab, M, tab, rep=f"{RAC}/contenu"):
    os.makedirs(rep, exist_ok=True)
    lignes, ncol = lignes_page(pg, lab, M, tab)
    sup=lignes_plus().get(pg)
    if sup:
        par={t[0]:t for t in lignes}
        for k,txt in sorted(sup.items()):
            # Ligne deja lue mais TRONQUEE a droite : on garde ses filets de
            # soulignement, qui portent sur le debut, et on rend le texte
            # entier. Ligne absente : on la cree, sans filet.
            plages = par[k][2] if k in par else []
            cells=list(txt) + [" "]*max(0, ncol-len(txt))
            par[k]=(k, cells, plages)
        # Le lattis est DENSE : une entree par interligne, blanche ou non.
        # Les lignes rendues peuvent laisser un trou — l'interligne vide qui
        # separe deux articles —, qu'il faut recreer, sinon les articles se
        # touchent et la page se decale d'une ligne. Un indice NEGATIF rend une
        # ligne perdue au-dessus de la premiere : le lattis s'etend vers le
        # haut, et la numerotation des lignes deja lues ne bouge pas.
        lignes=[par.get(k, (k, [" "]*ncol, []))
                for k in range(min(par), max(par)+1)]
    # Le lattis de lignes couvre toute la hauteur de l'image pour attraper les
    # folios ; en bas de page il produit donc des lignes fantomes, vides. Une
    # ligne vide APRES la derniere ligne encree ne porte aucune information et
    # ferait deborder la page composee (\vbox trop haute). On les retranche.
    def _vide(t):
        k,cells,plages = t
        return not plages and all(c==" " for c in cells)
    while lignes and _vide(lignes[-1]): lignes.pop()
    # Assiette de la page : on la centre sur sa propre largeur, avec un peu
    # plus de marge du cote de la couture. Une origine fixe laissait jusqu'a
    # 66 mm de blanc d'un cote et faisait deborder l'autre.
    # Une moucheture isolee loin a droite — un « - » seul apres vingt-quatre
    # espaces — n'est pas du texte : elle elargissait la page de trente
    # millimetres. On la retranche, sous condition stricte : un seul caractere,
    # de ponctuation, separe du reste par dix cases au moins.
    ISOLES=set("-.,'\"")
    for k,cells,plages in lignes:
        fin=-1
        for j in range(len(cells)-1,-1,-1):
            if cells[j]!=" ": fin=j; break
        if fin<1 or cells[fin] not in ISOLES: continue
        if any(b>=fin for a,b in plages): continue
        vide=0; j=fin-1
        while j>=0 and cells[j]==" ": vide+=1; j-=1
        if vide>=10: cells[fin]=" "
    dernier=0
    for k,cells,plages in lignes:
        fin=-1
        for j in range(len(cells)-1, -1, -1):
            if cells[j] != " ": fin=j; break
        if fin<0: continue
        dernier=max(dernier, fin)
        # Un filet qui depasse le dernier caractere de sa ligne est un artefact
        # de mesure : il ne doit pas elargir la page.
        for a,b in plages: dernier=max(dernier, min(b, fin))
    larg=(dernier+1)*PASH_MM
    haut=len(lignes)*PASV_MM
    # Origine FIXE, et non centrage page par page. Centrer chaque page sur sa
    # propre largeur la rendait equilibree isolement, mais faisait sauter le
    # bord gauche d'une page a l'autre : sur 631 pages, 199 sautaient de plus de
    # cinq millimetres, jusqu'a vingt-huit. Un livre ne fait pas cela — son bloc
    # de texte est a la meme place sur toutes les pages de meme main, et les
    # lignes courtes laissent simplement du blanc a droite.
    recto = (pg % 2 == 0)                    # page de droite dans le fac-simile
    if recto:
        x = LARG_MM - BORD_EXT - larg        # cale sur la tranche de droite
        if x < GOUTTIERE_MIN: x = GOUTTIERE_MIN
    else:
        x = BORD_EXT                         # cale sur la tranche de gauche
        if LARG_MM - x - larg < GOUTTIERE_MIN:
            x = LARG_MM - GOUTTIERE_MIN - larg
    # Les rares pages tres larges — six passent 74 colonnes — ne tiennent ni
    # la tranche ni la gouttiere. On leur laisse la butee absolue.
    if x + larg > LARG_MM - MARGE_EXTREME:
        x = max(LARG_MM - MARGE_EXTREME - larg, MARGE_EXTREME)
    x = max(x, MARGE_EXTREME)
    y = BORD_HAUT
    if y + haut > HAUT_MM - MARGE_BAS_MIN:
        y = max(HAUT_MM - MARGE_BAS_MIN - haut, MARGE_EXTREME)
    # Le decalage est quantifie sur la grille : un nombre entier de pas en
    # largeur, un nombre entier d'interlignes en hauteur. Sans cela les
    # caracteres ne tombent plus sur une colonne entiere, et le controle de
    # position — qui garantit la fidelite de la trame — echoue.
    dx=round((x-ORIGX_MM)/PASH_MM)*PASH_MM
    dy=round((y-ORIGY_MM)/PASV_MM)*PASV_MM
    L=["% page "+str(pg+1)+" du fac-simile (image p-%03d du scan)"%pg,
       "%% bloc %.1f x %.1f mm ; marge gauche %.1f mm"%(larg,haut,x),
       "\\pgc{%.3fmm}{%.3fmm}{"%(dx,dy)]
    for k,cells,plages in lignes:
        L.append("\\l{"+texifier(cells,plages)+"}")
    L.append("}")
    open(f"{rep}/p{pg:03d}.tex","w",encoding='utf-8').write("\n".join(L)+"\n")
    return len(lignes)
