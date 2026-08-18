# -*- coding: utf-8 -*-
"""Releve des vedettes qui rompent l'ordre alphabetique du livre.

Le livre est trie, et il l'est selon une regle qu'il n'enonce pas : LA
DESINENCE NE COMPTE PAS. « aktinio » precede « aktinika » parce que l'auteur
range « aktini » avant « aktinik ». L'edition garde les deux lectures — mot
entier et racine — et ne signale que ce qui recule sur les DEUX (voir
drapeli_ordino dans edition.py).

Ce qui reste demande un oeil sur le fac-simile. Le fichier rendu prepare ce
travail : pour chaque cas, il donne la page et la ligne de la grille, les
vedettes voisines, la place ou la vedette aurait du aller, et — quand une
mauvaise lecture expliquerait tout — les lectures qui tiendraient dans la place
occupee, formees avec les confusions que le journal des corrections a relevees.

    python3 outils/releve_ordino.py
"""
import json, sys, collections

RAC = "/root/dicionario"
SOURCE = f"{RAC}/dicionario.jsonl"
SORTIE = f"{RAC}/ordino-ruptita.md"
sys.path.insert(0, f"{RAC}/outils")
import edition as E

# Les confusions du decodage, relevees dans travail/journal_complet.txt : la
# lettre lue, la lettre retenue, et le nombre de fois. On ne garde que les plus
# frequentes — ce sont elles qui expliquent une vedette fautive.
def konfuzoj(fichier=f"{RAC}/travail/journal_complet.txt", minimo=15):
    c = collections.Counter()
    try:
        for l in open(fichier, encoding='utf-8'):
            if l.startswith('#'):
                continue
            p = l.rstrip('\n').split('\t')
            if len(p) >= 5 and len(p[3]) == 1 and len(p[4]) == 1:
                c[(p[3].lower(), p[4].lower())] += 1
    except OSError:
        return {}
    out = collections.defaultdict(set)
    for (a, b), n in c.items():
        if n >= minimo and a != b:
            out[a].add(b)
            out[b].add(a)
    return out


VOKALI = 'aeiou'


def plausibla(v, mot):
    """La lecture a-t-elle la forme d'un mot ido ?

    On ecarte ce que la substitution fabrique de mecanique : une voyelle
    doublee que l'original n'avait pas — « brooho » pour « brocho » —, et une
    finale qui n'est pas celle d'un mot de la langue.
    """
    if not any(v.endswith(f) for f in E.FINALES_OK) and not v.endswith(mot[-1]):
        return False
    for a in VOKALI:
        if a + a in v and a + a not in mot:
            return False
    return True


def variantoj(mot, konf, lexiko=()):
    """Les lectures voisines : une lettre confondue, ou deux interverties."""
    out = set()
    for i, c in enumerate(mot):
        for d in konf.get(c, ()):
            out.add(mot[:i] + d + mot[i+1:])
        if i + 1 < len(mot) and mot[i] != mot[i+1]:
            out.add(mot[:i] + mot[i+1] + mot[i] + mot[i+2:])
        # La lettre de trop : la dactylo frappe deux fois, ou le decodage lit un
        # signe dans une tache. « ostegomo » pour « osteomo ».
        if len(mot) > 4:
            out.add(mot[:i] + mot[i+1:])
    out.discard(mot)
    return sorted(v for v in out if plausibla(v, mot))


def ecrire(source=SOURCE, sortie=SORTIE):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    K = [E._klavo_ordino(e['vedetto']) for e in ent]
    R = [E._klavo_radiko(e['vedetto']) for e in ent]
    konf = konfuzoj()
    # Le lexique du livre : ses vedettes et les mots de ses definitions. Une
    # lecture qu'il atteste ailleurs vaut mieux qu'une forme fabriquee.
    import re as _re
    lexiko = {e['vedetto'].lower().lstrip('*') for e in ent}
    for e in ent:
        for t in e.get('senci') or []:
            lexiko.update(w.lower() for w in _re.findall(r"[A-Za-zÀ-ÿ'’-]{3,}", t))

    def rupto(a, b):
        return K[b] < K[a] and R[b] < R[a]

    def monotona(idx):
        return all(not rupto(idx[t-1], idx[t]) for t in range(1, len(idx)))

    def loko(e):
        return "f.%s (image %s, ligne %s)" % (e['pagino'], e['image'], e['ligno'])

    def place(k, r, saut):
        """Ou cette cle irait-elle ? Rend l'indice du premier article qui la suit."""
        for j in range(len(ent)):
            if j in saut:
                continue
            if R[j] > r or (R[j] == r and K[j] > k):
                return j
        return len(ent)

    inversi, egari = [], []
    for i, e in enumerate(ent):
        if 'ordino-ruptita' not in e['drapeli']:
            continue
        fen = list(range(max(0, i-3), min(len(ent), i+4)))
        permut = [j for j in fen]
        a = permut.index(i-1); permut[a], permut[a+1] = permut[a+1], permut[a]
        if monotona(permut):
            inversi.append(i)
        else:
            egari.append(i)

    L = ["# Vedettes qui rompent l'ordre alphabetique", "",
         "Le livre est trie, et il l'est selon une regle qu'il n'enonce pas : **la",
         "desinence ne compte pas**. « aktinio » precede « aktinika » parce que",
         "l'auteur range « aktini » avant « aktinik ». L'auteur ne s'y tient pas",
         "partout — il ecrit « astrakano » puis « astro » —, et le drapeau ne se",
         "leve donc que si la vedette recule sur LES DEUX lectures, mot entier et",
         "racine.",
         "",
         f"**{len(inversi) + len(egari)} cas**, sur {len(ent)} articles. Deux familles :",
         "les deux vedettes voisines qu'il suffit d'intervertir, et la vedette",
         "posee loin de sa place — celle-la est souvent une mauvaise lecture.",
         "",
         "Chaque cas donne le folio imprime, l'image du fac-simile et la ligne de",
         "la grille, pour aller voir.",
         ""]

    L += [f"## Deux vedettes voisines interverties — {len(inversi)}", "",
          "L'ordre du livre voudrait la seconde d'abord. Rien d'autre ne cloche :",
          "les deux vedettes sont a leur page, et leurs voisines sont en ordre.",
          "",
          "| folio | image:ligne | telles qu'ecrites | dans l'ordre |",
          "|---|---|---|---|"]
    for i in inversi:
        a, b = ent[i-1], ent[i]
        L.append("| %s | %s:%s | %s, %s | %s, %s |"
                 % (b['pagino'], b['image'], b['ligno'],
                    a['vedetto'], b['vedetto'], b['vedetto'], a['vedetto']))
    L.append("")

    L += [f"## Une vedette loin de sa place — {len(egari)}", ""]
    for i in egari:
        fen = list(range(max(0, i-3), min(len(ent), i+4)))
        sansB = [j for j in fen if j != i]
        sansA = [j for j in fen if j != i-1]
        cand = []
        if monotona(sansB):
            cand.append(i)
        if monotona(sansA):
            cand.append(i-1)
        if not cand:
            cand = [i]
        for x in cand:
            e = ent[x]
            j = place(K[x], R[x], {x})
            avan = ent[j-1] if j > 0 else None
            L += ["### %s — %s" % (e['vedetto'], loko(e)), "",
                  "Ecrite entre « %s » et « %s »." % (
                      ent[x-1]['vedetto'] if x else '(debut)',
                      ent[x+1]['vedetto'] if x+1 < len(ent) else '(fin)'),
                  ""]
            if avan is not None and abs(j - x) > 1:
                L += ["Sa place est apres « %s », %s — %d articles plus %s."
                      % (avan['vedetto'], loko(avan), abs(j - x),
                         "loin" if j > x else "haut"), ""]
            elif avan is not None:
                L += ["Sa place est juste avant « %s », sa voisine."
                      % ent[x-1]['vedetto'], ""]
            # La lecture proposee ne peut pas etre celle d'une vedette voisine :
            # le livre ne definit pas deux fois le meme mot a trois lignes de
            # distance. « arterito » n'est pas « arterio », qui le precede.
            proxima = {K[j] for j in range(max(0, x-3), min(len(ent), x+4))}
            var = [v for v in variantoj(K[x], konf)
                   if (x == 0 or K[x-1] <= v) and (x+1 >= len(ent) or v <= K[x+1])
                   and v not in proxima]
            if var:
                L += ["Lectures qui tiendraient dans la place occupee : %s."
                      % ", ".join("**%s**%s" % (v, " (mot atteste ailleurs)"
                                                if v in lexiko else "")
                                  for v in var[:8]), ""]
            L += ["```", (e.get('teksto_brut') or '')[:200], "```", ""]

    open(sortie, "w", encoding='utf-8').write("\n".join(L) + "\n")
    print("%s : %d interversions, %d vedettes egarees"
          % (sortie, len(inversi), len(egari)))


if __name__ == "__main__":
    ecrire()
