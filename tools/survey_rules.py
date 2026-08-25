# -*- coding: utf-8 -*-
"""A survey of the underlines the edition could not place.

The typescript has no italic: the typist underlines. The edition reads those
rules and makes of them the italic of the domain, the bold of the phrase.
Some rules will not be placed: the stroke runs over the punctuation, stops in
the middle of a word, or covers a function word only. These are artefacts of
the survey, not intentions of the author -- but one must be able to judge.

The file returned classes them by family, the most doubtful at the head, with
the page and the headword so that the facsimile can be consulted.

    python3 tools/survey_rules.py
"""
import json, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edition

ROOT = "/root/dicionario"
SOURCE = f"{ROOT}/dicionario.jsonl"
OUT_PATH = f"{ROOT}/filets-dubinda.md"

# The list of function words is the edition's own, `edition.MALGRANDA`: it is
# that list which decides NOT to lay the italic, and this working list must
# class by the same rule, failing which the fragments it sets aside turn up
# here in a family other than their own.


def famille(u):
    """What does the fragment look like?"""
    words = u.split()
    if len(u) <= 3:
        return "2. Fragment de trois lettres ou moins"
    if not re.fullmatch(r"[A-Za-zÀ-ÿ'’ .,()-]+", u):
        return "2. Fragment de trois lettres ou moins"
    if edition._nur_motouti(u):
        return "3. Mots-outils seuls"
    if u[0].isupper() and len(words) <= 4:
        return "1. Ressemble a un qualificatif ou a une locution"
    return "4. Coupe au milieu d'un mot, ou reste du mot-vedette"


def write_(source=SOURCE, out_path=OUT_PATH):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    per = collections.defaultdict(list)
    for e in ent:
        for u in e.get('dubinda', []):
            per[famille(u)].append((e['pagino'], e['vedetto'], u))
    total = sum(len(v) for v in per.values())
    L = ["# Soulignements non places",
         "",
         "L'auteur souligne ce qu'une imprimerie mettrait en italique : le",
         "domaine, la locution qui porte sa propre definition, le nom",
         "scientifique. L'edition epuree lit ces filets et les rend. Voici ceux",
         "qu'elle n'a pas su placer : le fragment releve ne se retrouve pas tel",
         "quel dans le texte, ou ne couvre que des mots-outils.",
         "",
         f"**{total} fragments**, sur {len(ent)} articles. La premiere famille est",
         "la seule qui demande un arbitrage : les autres sont des artefacts du",
         "releve des filets, ou le trait deborde ou s'arrete trop tot.",
         ""]
    for fam in sorted(per):
        v = sorted(per[fam])
        L += [f"## {fam[3:]} — {len(v)}", "",
              "| page | mot-vedette | fragment souligne |",
              "|---:|---|---|"]
        for p, hw, u in v:
            L.append(f"| {p} | {hw} | `{u}` |")
        L.append("")
    open(out_path, "w", encoding='utf-8').write("\n".join(L) + "\n")
    return total, {k: len(v) for k, v in per.items()}


if __name__ == "__main__":
    n, d = write_()
    print("fragments not placed:", n)
    for k in sorted(d):
        print("   %-58s %d" % (k, d[k]))
