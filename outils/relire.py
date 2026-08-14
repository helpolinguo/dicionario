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


def appliquer(ent, dossier=DOSSIER):
    """Pose les corrections de relecture. Rend (posees, refusees)."""
    cor = lire(dossier)
    if not cor:
        return 0, 0
    pose = 0; refus = 0
    for a, b, lot in cor:
        vus = []
        for e in ent:
            for k, t in enumerate(e.get('senci') or []):
                if a in t:
                    vus.append((e, k))
            # Le domaine est un champ a part : « (ariktekt) » n'est dans aucun
            # sens, et la correction etait refusee faute de le chercher la.
            f = e.get('fako')
            if f and a.strip('()') in f:
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
                e['fako'] = e['fako'].replace(a.strip('()'), b.strip('()'))
            else:
                e['senci'][k] = e['senci'][k].replace(a, b)
            pose += 1
    return pose, refus
