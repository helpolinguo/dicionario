# -*- coding: utf-8 -*-
"""Couche de relecture des definitions, article par article.

Les detecteurs structurels sont epuises. Ce qui reste — « vaormashino » pour
« vapormashino », « fibranta » pour « vibranta », « kuh » pour « kun » — ne se
voit qu'en lisant la phrase. Le livre est donc decoupe en lots de 130 articles
(outils/planches_relire.py), relus un lot a la fois, et les corrections sont
deposees ici.

L'identifiant rendu par la relecture n'est PAS utilise pour appliquer la
correction. Il derive de la position dans le fichier, or cette position bouge
des qu'un article s'ajoute — la reparation du bas de page en a ajoute quatre.
On cherche donc la chaine fautive elle-meme, et on n'applique que si elle est
UNIQUE dans le livre : une chaine ambigue est refusee plutot que posee au
hasard. Les chaines rendues font plusieurs mots, ce qui suffit a les distinguer.
"""
import os, re, glob
T = "/root/dicionario/travail"
DOSSIER = f"{T}/relire/reponses"


def lire(dossier=DOSSIER):
    """Toutes les corrections rendues : liste de (fautif, correct, lot)."""
    out = []
    for p in sorted(glob.glob(f"{dossier}/*.txt")):
        lot = os.path.basename(p)[:-4]
        for l in open(p, encoding='utf-8'):
            l = l.rstrip("\n")
            if not l.strip() or l.startswith("#") or l.strip() == "RIEN":
                continue
            ch = l.split("\t")
            if len(ch) < 3:
                continue
            a, b = ch[-2].strip(), ch[-1].strip()
            # Une relecture rend parfois une ligne de prose au lieu d'une
            # correction — « apofizo<TAB>... », « check done ». On refuse ce
            # qui n'a pas la forme d'un remplacement : ellipse, chaine vide,
            # ou cible bien plus courte que la source.
            if not a or not b or a == b: continue
            if '...' in b or '…' in b: continue
            if len(b) < len(a) * 0.5: continue
            out.append((a, b, lot))
    return out


_ESP = r"[\s\u00a0]*"

def _motif(a):
    """Regex de la chaine fautive, indifferente a l'espacement."""
    out = []
    n = len(a)
    for i, c in enumerate(a):
        bord = (i == 0 or i == n - 1)
        if c.isspace():
            if out and out[-1] == _ESP + "+":
                continue
            out.append(_ESP + "+")
        elif c in "\u00ab\u00bb:;!?()":
            # Aux BORDS de la chaine, ne pas absorber l'espace voisin : il ne
            # serait pas rendu par le remplacement, et deux mots se colleraient.
            g = "" if i == 0 else _ESP
            d = "" if i == n - 1 else _ESP
            out.append(g + re.escape(c) + d)
        else:
            out.append(re.escape(c))
    return re.compile("".join(out))


def appliquer(ent, dossier=DOSSIER):
    """Pose les corrections de relecture. Rend (posees, refusees)."""
    cor = lire(dossier)
    if not cor:
        return 0, 0
    pose = 0; refus = 0
    for a, b, lot in cor:
        # La chaine fautive a ete relevee AVANT que la typographie soit posee :
        # les chevrons et le deux-points ont depuis gagne une espace insecable,
        # « grande » s'ecrit « \u00ab\u00a0grande\u00a0\u00bb ». Cherchee au
        # caractere pres, la correction ne se retrouvait plus. On rend donc la
        # recherche indifferente a l'espacement autour de la ponctuation.
        mot = _motif(a)
        vus = []
        for e in ent:
            for k, t in enumerate(e.get('senci') or []):
                if mot.search(t):
                    vus.append((e, k))
            # Le domaine est un champ a part : « (ariktekt) » n'est dans aucun
            # sens, et la correction etait refusee faute de le chercher la.
            #
            # Le champ est rendu en MINUSCULES (edition.minuskligi) alors que la
            # relecture recopie la page : « Yorocienco » chez « prekara » ne se
            # retrouvait pas dans « yorocienco », et la correction — la seule qui
            # portait sur ce mot — etait refusee en silence. La comparaison
            # ignore donc la casse, de part et d'autre.
            f = e.get('fako')
            if f and re.search(re.escape(a.strip('()')), f, re.I):
                vus.append((e, 'fako'))
        # Une meme coquille se repete parfois a l'identique — « pseupodi » deux
        # fois, « di sapto » deux fois. La refuser serait perdre une correction
        # juste. On l'applique donc partout, mais SEULEMENT si la chaine est
        # assez distinctive pour ne pas happer autre chose : au moins six
        # caracteres, ou plusieurs mots. « lO », vu onze fois, reste refuse.
        if not vus or (len(vus) > 1 and len(a) < 6 and ' ' not in a):
            refus += 1
            print("  relire %s : «%s» vu %d fois — refuse" % (lot, a[:40], len(vus)))
            continue
        for e, k in vus:
            if k == 'fako':
                e['fako'] = re.sub(re.escape(a.strip('()')),
                                   lambda _m: b.strip('()'), e['fako'], flags=re.I)
            else:
                e['senci'][k] = mot.sub(lambda _m: b, e['senci'][k], count=1)
            pose += 1
    return pose, refus
