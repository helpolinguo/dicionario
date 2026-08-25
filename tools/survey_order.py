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
OUT_PATH = f"{ROOT}/docs/order-broken.md"
import edition as E

# The decoding's confusions, surveyed in work/journal_full.txt: the letter
# read, the letter adopted, and how many times. We keep only the most frequent
# -- they are the ones that explain a faulty headword.
def confusions(file_=f"{ROOT}/work/journal_full.txt", minimum_=15):
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
        if n >= minimum_ and a != b:
            out[a].add(b)
            out[b].add(a)
    return out


VOWELS = 'aeiou'


def plausible(v, word):
    """Has the reading the shape of an Ido word?

    We set aside what the substitution manufactures mechanically: a doubled
    vowel the original did not have -- « brooho » for « brocho » -- and an
    ending that is not that of a word of the language.
    """
    if not any(v.endswith(f) for f in E.ENDINGS_OK) and not v.endswith(word[-1]):
        return False
    for a in VOWELS:
        if a + a in v and a + a not in word:
            return False
    return True


def variants_(word, confs, lexicon=()):
    """The neighbouring readings: one letter confused, or two transposed."""
    out = set()
    for i, c in enumerate(word):
        for d in confs.get(c, ()):
            out.add(word[:i] + d + word[i+1:])
        if i + 1 < len(word) and word[i] != word[i+1]:
            out.add(word[:i] + word[i+1] + word[i] + word[i+2:])
        # The letter too many: the typist strikes twice, or the decoding reads a
        # sign in a spot. « ostegomo » for « osteomo ».
        if len(word) > 4:
            out.add(word[:i] + word[i+1:])
    out.discard(word)
    return sorted(v for v in out if plausible(v, word))


def write_(source=SOURCE, out_path=OUT_PATH):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    K = [E._order_key(e['vedetto']) for e in ent]
    R = [E._root_key(e['vedetto']) for e in ent]
    confs = confusions()
    # The book's lexicon: its headwords and the words of its definitions. A
    # reading it attests elsewhere is worth more than a manufactured form.
    import re as _re
    lexicon = {e['vedetto'].lower().lstrip('*') for e in ent}
    for e in ent:
        for t in e.get('senci') or []:
            lexicon.update(w.lower() for w in _re.findall(r"[A-Za-zÀ-ÿ'’-]{3,}", t))

    def breaks_at(a, b):
        return K[b] < K[a] and R[b] < R[a]

    def monotonic(idx):
        return all(not breaks_at(idx[t-1], idx[t]) for t in range(1, len(idx)))

    def spot(e):
        return "f.%s (image %s, line %s)" % (e['pagino'], e['image'], e['ligno'])

    def place(k, r, skip):
        """Where would this key go? Returns the index of the first article after it."""
        for j in range(len(ent)):
            if j in skip:
                continue
            if R[j] > r or (R[j] == r and K[j] > k):
                return j
        return len(ent)

    swapped, astray = [], []
    for i, e in enumerate(ent):
        if 'ordino-ruptita' not in e['drapeli']:
            continue
        window_ = list(range(max(0, i-3), min(len(ent), i+4)))
        permuted = [j for j in window_]
        a = permuted.index(i-1); permuted[a], permuted[a+1] = permuted[a+1], permuted[a]
        if monotonic(permuted):
            swapped.append(i)
        else:
            astray.append(i)

    L = ["# Headwords that break the alphabetical order", "",
         "The book is sorted, and sorted by a rule it never states: **the",
         "ending does not count**. « aktinio » precedes « aktinika » because",
         "the author files « aktini » before « aktinik ». He does not hold to",
         "it everywhere -- he writes « astrakano » and then « astro » -- so the",
         "flag is raised only when the headword goes backwards on BOTH",
         "readings, whole word and root.",
         "",
         f"**{len(swapped) + len(astray)} cases**, over {len(ent)} entries. Two families:",
         "the two neighbouring headwords one need only swap, and the headword",
         "laid far from its place -- that one is often a misreading.",
         "",
         "Each case gives the printed folio, the facsimile image and the line",
         "of the grid, so that it can be looked up.",
         ""]

    L += [f"## Two neighbouring headwords swapped — {len(swapped)}", "",
          "The book's order would have the second first. Nothing else is wrong:",
          "both headwords are on their page, and their neighbours are in order.",
          "",
          "| folio | image:line | as written | in order |",
          "|---|---|---|---|"]
    for i in swapped:
        a, b = ent[i-1], ent[i]
        L.append("| %s | %s:%s | %s, %s | %s, %s |"
                 % (b['pagino'], b['image'], b['ligno'],
                    a['vedetto'], b['vedetto'], b['vedetto'], a['vedetto']))
    L.append("")

    L += [f"## A headword far from its place — {len(astray)}", ""]
    for i in astray:
        window_ = list(range(max(0, i-3), min(len(ent), i+4)))
        withoutB = [j for j in window_ if j != i]
        withoutA = [j for j in window_ if j != i-1]
        cand = []
        if monotonic(withoutB):
            cand.append(i)
        if monotonic(withoutA):
            cand.append(i-1)
        if not cand:
            cand = [i]
        for x in cand:
            e = ent[x]
            j = place(K[x], R[x], {x})
            ahead = ent[j-1] if j > 0 else None
            L += ["### %s — %s" % (e['vedetto'], spot(e)), "",
                  "Written between « %s » and « %s »." % (
                      ent[x-1]['vedetto'] if x else '(start)',
                      ent[x+1]['vedetto'] if x+1 < len(ent) else '(end)'),
                  ""]
            if ahead is not None and abs(j - x) > 1:
                L += ["Its place is after « %s », %s — %d entries further %s."
                      % (ahead['vedetto'], spot(ahead), abs(j - x),
                         "down" if j > x else "up"), ""]
            elif ahead is not None:
                L += ["Its place is just before « %s », its neighbour."
                      % ent[x-1]['vedetto'], ""]
            # The reading proposed cannot be that of a neighbouring headword: the
            # book does not define the same word twice three lines apart.
            # « arterito » is not « arterio », which precedes it.
            nearest = {K[j] for j in range(max(0, x-3), min(len(ent), x+4))}
            var = [v for v in variants_(K[x], confs)
                   if (x == 0 or K[x-1] <= v) and (x+1 >= len(ent) or v <= K[x+1])
                   and v not in nearest]
            if var:
                L += ["Readings that would fit the place occupied: %s."
                      % ", ".join("**%s**%s" % (v, " (word attested elsewhere)"
                                                if v in lexicon else "")
                                  for v in var[:8]), ""]
            L += ["```", (e.get('teksto_brut') or '')[:200], "```", ""]

    open(out_path, "w", encoding='utf-8').write("\n".join(L) + "\n")
    print("%s : %d transpositions, %d headwords astray"
          % (out_path, len(swapped), len(astray)))


if __name__ == "__main__":
    write_()
