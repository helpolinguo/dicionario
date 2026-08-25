# -*- coding: utf-8 -*-
"""A survey of the headwords that break the book's alphabetical order.

The book is sorted, and it is sorted by a rule it does not state: THE ENDING
DOES NOT COUNT. « aktinio » precedes « aktinika » because the author files
« aktini » before « aktinik ». The edition keeps both readings -- whole word
and root -- and reports only what goes backwards on BOTH (see drapeli_ordino
in edition.py).

What is left calls for an eye on the facsimile. The file returned prepares
that work: for each case it gives the page and the line of the grid, the
neighbouring headwords, the place the headword should have gone, and -- when a
misreading would explain everything -- the readings that would fit the place
occupied, formed with the confusions the log of corrections has recorded.

    python3 tools/survey_order.py
"""
import json, sys, collections
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = _ROOT
SOURCE = f"{ROOT}/dicionario.jsonl"
OUT_PATH = f"{ROOT}/ordino-ruptita.md"
sys.path.insert(0, f"{ROOT}/tools")
import edition as E

# The decoding's confusions, surveyed in work/journal_complet.txt: the letter
# read, the letter adopted, and how many times. We keep only the most frequent
# -- they are the ones that explain a faulty headword.
def konfuzoj(file_=f"{ROOT}/work/journal_complet.txt", minimo=15):
    c = collections.Counter()
    try:
        for l in open(file_, encoding='utf-8'):
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


def plausibla(v, word):
    """Has the reading the shape of an Ido word?

    We set aside what the substitution manufactures mechanically: a doubled
    vowel the original did not have -- « brooho » for « brocho » -- and an
    ending that is not that of a word of the language.
    """
    if not any(v.endswith(f) for f in E.FINALES_OK) and not v.endswith(word[-1]):
        return False
    for a in VOKALI:
        if a + a in v and a + a not in word:
            return False
    return True


def variantoj(word, konf, lexiko=()):
    """The neighbouring readings: one letter confused, or two transposed."""
    out = set()
    for i, c in enumerate(word):
        for d in konf.get(c, ()):
            out.add(word[:i] + d + word[i+1:])
        if i + 1 < len(word) and word[i] != word[i+1]:
            out.add(word[:i] + word[i+1] + word[i] + word[i+2:])
        # The letter too many: the typist strikes twice, or the decoding reads a
        # sign in a spot. « ostegomo » for « osteomo ».
        if len(word) > 4:
            out.add(word[:i] + word[i+1:])
    out.discard(word)
    return sorted(v for v in out if plausibla(v, word))


def write_(source=SOURCE, out_path=OUT_PATH):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    K = [E._klavo_ordino(e['vedetto']) for e in ent]
    R = [E._klavo_radiko(e['vedetto']) for e in ent]
    konf = konfuzoj()
    # The book's lexicon: its headwords and the words of its definitions. A
    # reading it attests elsewhere is worth more than a manufactured form.
    import re as _re
    lexiko = {e['vedetto'].lower().lstrip('*') for e in ent}
    for e in ent:
        for t in e.get('senci') or []:
            lexiko.update(w.lower() for w in _re.findall(r"[A-Za-zÀ-ÿ'’-]{3,}", t))

    def rupto(a, b):
        return K[b] < K[a] and R[b] < R[a]

    def monotona(idx):
        return all(not rupto(idx[t-1], idx[t]) for t in range(1, len(idx)))

    def spot(e):
        return "f.%s (image %s, ligne %s)" % (e['pagino'], e['image'], e['ligno'])

    def place(k, r, saut):
        """Where would this key go? Returns the index of the first article after it."""
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
            ahead = ent[j-1] if j > 0 else None
            L += ["### %s — %s" % (e['vedetto'], spot(e)), "",
                  "Ecrite entre « %s » et « %s »." % (
                      ent[x-1]['vedetto'] if x else '(debut)',
                      ent[x+1]['vedetto'] if x+1 < len(ent) else '(fin)'),
                  ""]
            if ahead is not None and abs(j - x) > 1:
                L += ["Sa place est apres « %s », %s — %d articles plus %s."
                      % (ahead['vedetto'], spot(ahead), abs(j - x),
                         "loin" if j > x else "haut"), ""]
            elif ahead is not None:
                L += ["Sa place est juste avant « %s », sa voisine."
                      % ent[x-1]['vedetto'], ""]
            # The reading proposed cannot be that of a neighbouring headword: the
            # book does not define the same word twice three lines apart.
            # « arterito » is not « arterio », which precedes it.
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

    open(out_path, "w", encoding='utf-8').write("\n".join(L) + "\n")
    print("%s : %d transpositions, %d headwords astray"
          % (out_path, len(inversi), len(egari)))


if __name__ == "__main__":
    write_()
