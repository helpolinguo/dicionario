# -*- coding: utf-8 -*-
"""Dicionario de posho — edituro moderna, en LaTeX.

Ce n'est pas le fac-simile : c'est le TEXTE EPURE, celui de la page HTML,
compose comme un dictionnaire de poche d'aujourd'hui — deux colonnes, titre
courant donnant le premier mot-vedette a gauche et le dernier a droite,
lettrines de section.

La source est le meme fichier que la page HTML,
travail/edicioni/dicionario.jsonl. Les deux editions ne peuvent donc pas
diverger : toute correction posee dans les couches de relecture se retrouve
dans l'une comme dans l'autre des la reconstruction suivante.
"""
import json, os, re, unicodedata

RAC = "/root/dicionario"; T = f"{RAC}/travail"; OUT = f"{RAC}/posho"
SOURCE = f"{T}/edicioni/dicionario.jsonl"

# Le tapuscrit note les langues par une lettre ; l'edition de lecture les
# ecrit au long. En poche, la place manque : on revient a l'abrege, mais
# lisible.
ABREGE = {'Germana': 'D', 'Angla': 'E', 'Franca': 'F', 'Italiana': 'I',
          'Rusa': 'R', 'Hispana': 'S', 'Latina': 'L', 'Portugalana': 'P',
          'Greka': 'G', 'Nederlandana': 'N'}


def esc(t):
    """Texte vers LaTeX. La source contient des chevrons, des tirets longs et
    des espaces insecables qu'il faut garder tels quels."""
    if t is None:
        return ""
    for a, b in (('\\', r'\textbackslash{}'), ('{', r'\{'), ('}', r'\}'),
                 ('&', r'\&'), ('%', r'\%'), ('$', r'\$'), ('#', r'\#'),
                 ('_', r'\_'), ('^', r'\textasciicircum{}'),
                 ('~', r'\textasciitilde{}')):
        t = t.replace(a, b)
    return t


def cle(v):
    """Cle de classement : sans asterisque, sans accent, sans tiret."""
    v = v.lstrip('*-')
    v = unicodedata.normalize('NFD', v)
    v = ''.join(c for c in v if unicodedata.category(c) != 'Mn')
    return v.lower()


def artiklo(e):
    """Un article, en LaTeX."""
    v = e['vedetto']
    # Emprunt cite : le tapuscrit l'encadre de guillemets. On les rend.
    aff = "\u00ab\u00a0%s\u00a0\u00bb" % v if e.get('citita') else v
    L = ["\\vorto{%s}" % esc(aff)]
    if e.get('fako'):
        L.append("\\fako{%s}" % esc(e['fako']))
    S = e.get('senci') or []
    if len(S) > 1:
        for i, s in enumerate(S):
            L.append("\\senco{%d}{%s}" % (i + 1, esc(s)))
    elif S:
        L.append(" " + esc(S[0]))
    if e.get('latina'):
        L.append("\\latina{%s}" % esc('; '.join(e['latina'])))
    if e.get('lingui'):
        code = ''.join(ABREGE.get(x, '') for x in e['lingui'])
        if code:
            L.append("\\lingui{%s}" % esc(code))
    return "\\artiklo{%s}%%\n" % esc(v) + "".join(L)


def ecrire(source=SOURCE, dossier=OUT):
    os.makedirs(dossier, exist_ok=True)
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    ent.sort(key=lambda e: (cle(e['vedetto']), e['image'], e['ligno']))
    lignes = []
    lettre = None
    for e in ent:
        k = cle(e['vedetto'])
        c = k[0].upper() if k else '?'
        if c != lettre and c.isalpha():
            lettre = c
            lignes.append("\\sekciono{%s}" % c)
        lignes.append(artiklo(e))
    with open(f"{dossier}/enhavo.tex", "w", encoding='utf-8') as f:
        f.write("\n".join(lignes) + "\n")
    print("posho/enhavo.tex : %d artikli, %d sekcioni"
          % (len(ent), sum(1 for l in lignes if l.startswith("\\sekciono"))))
    return len(ent)


if __name__ == "__main__":
    ecrire()
