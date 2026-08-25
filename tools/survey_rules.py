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
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROOT = _ROOT
SOURCE = f"{ROOT}/dicionario.jsonl"
OUT_PATH = f"{ROOT}/docs/underlines-unplaced.md"

# The list of function words is the edition's own, `edition.MALGRANDA`: it is
# that list which decides NOT to lay the italic, and this working list must
# class by the same rule, failing which the fragments it sets aside turn up
# here in a family other than their own.


def family(u):
    """What does the fragment look like?"""
    words = u.split()
    if len(u) <= 3:
        return "2. Fragment of three letters or fewer"
    if not re.fullmatch(r"[A-Za-zÀ-ÿ'’ .,()-]+", u):
        return "2. Fragment of three letters or fewer"
    if edition._function_words_only(u):
        return "3. Function words alone"
    if u[0].isupper() and len(words) <= 4:
        return "1. Looks like a qualifier or a phrase"
    return "4. Cut in the middle of a word, or left over from the headword"


def write_(source=SOURCE, out_path=OUT_PATH):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    per = collections.defaultdict(list)
    for e in ent:
        for u in e.get('dubinda', []):
            per[family(u)].append((e['pagino'], e['vedetto'], u))
    total = sum(len(v) for v in per.values())
    L = ["# Underlines that could not be placed",
         "",
         "The author underlines what a printing house would set in italic:",
         "the domain, the phrase that carries its own definition, the",
         "scientific name. The clean edition reads those rules and renders",
         "them. Here are the ones it could not place: the fragment surveyed",
         "is not found as it stands in the text, or covers function words",
         "only.",
         "",
         f"**{total} fragments**, over {len(ent)} entries. The first family is",
         "the only one that calls for a judgement: the others are artefacts of",
         "the survey of the rules, where the stroke runs over or stops short.",
         ""]
    for fam in sorted(per):
        v = sorted(per[fam])
        L += [f"## {fam[3:]} — {len(v)}", "",
              "| page | headword | underlined fragment |",
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
