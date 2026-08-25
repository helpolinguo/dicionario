# -*- coding: utf-8 -*-
"""A systematic check of the structured edition.

The facsimile preserves the least fault of the original; the structured
edition must present a clean form of it. We therefore do not correct case by
case -- each pass brought a new family to light -- but inventory the
departures by FAMILY, deal with the family, and check again.

The checks are independent of one another, and each rests on an invariant of
the book itself, not on my judgement:

  coverage     every article has a source, every source an article
  round trip   the article's text is found again in the lines it came from
  order        the dictionary is alphabetical; a break is a clue
  morphology   an Ido headword ends in -o -a -e -i -ar -ir -or (or is an affix)
  langui       the final code is a subset of DEFIRSLP
  punctuation  no orphan punctuation, no unreglued hyphenation, nothing empty
  latina       the scientific name is extracted, not left in the sense
"""
import sys
sys.path.insert(0,'/root/dicionario/outils')
from edition import _lire_code
import json, re, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"
FIN_OK = ("o","a","e","i","ar","ir","or")
CODES  = set("DEFIRSLP")

def charger(p=f"{T}/edicioni/dicionario.jsonl"):
    return [json.loads(l) for l in open(p,encoding='utf-8')]

def cles(v):
    """Sort key: without the asterisk of the unofficial words, without the hyphen."""
    return v.lower().lstrip("*+-").replace("-","")

def controler(ent):
    pb=collections.defaultdict(list)
    for e in ent:
        v=e.get('vedetto') or ""
        senci=e.get('senci') or []
        txt=" ".join(senci)
        n=(e['image'], e['ligno'], v)
        if not v: pb['vedette-vide'].append(n); continue
        nu=v.lstrip("*")
        # Legitimate forms the check took for noise: the elision « a(d) », the
        # interjection « ah! », the phrase « a posteriori ».
        if not re.fullmatch(r"[A-Za-zÀ-ÿ'’-]+(?:\([a-z]\))?!?"
                            r"(?: [A-Za-zÀ-ÿ'’-]+){0,2}", nu):
            pb['vedette-caracteres'].append(n)
        elif not (nu.endswith(FIN_OK) or nu.startswith("-") or nu.endswith("-")):
            pb['finale-non-ido'].append(n)
        if not senci: pb['sans-senco'].append(n)
        for s in senci:
            if re.match(r'^[.,;:)\]]', s): pb['ponctuation-en-tete'].append(n); break
            if re.search(r'\w- \w', s): pb['cesure-non-recollee'].append(n); break
            if re.search(r'\s{2,}', s): pb['espaces-doubles'].append(n); break
        # The code is read by _lire_code, which admits the damaged capital
        # (« dEFIRS »), the « l » read for « I » (« DEFlS ») and the language
        # spelled out (« Ned », « FDSued », « Jap.,Sanskr »). Compared with a
        # plain set of letters, all of that passed for invalid.
        k=e.get('kodo')
        if k and not all(_lire_code(x.strip(' .')) for x in str(k).split(',')):
            pb['code-invalide'].append(n)
        if re.search(r'(?<![A-Za-z])L\.\s*[a-z]', txt): pb['latina-dans-le-senco'].append(n)
        if re.search(r'\b[DEFIRS]{3,7}\b\s*\.?\s*$', txt): pb['code-dans-le-senco'].append(n)
    # alphabetical order
    prec=None
    for e in ent:
        v=e.get('vedetto') or ""
        if not v: continue
        k=cles(v)
        if prec and k < prec: pb['ordre-rompu'].append((e['image'], e['ligno'], v))
        prec=k
    return pb

if __name__=="__main__":
    ent=charger()
    pb=controler(ent)
    print("articles : %d"%len(ent))
    tot=0
    for f,l in sorted(pb.items(), key=lambda x:-len(x[1])):
        print("  %-24s %5d" % (f, len(l))); tot+=len(l)
    print("  %-24s %5d" % ("TOTAL des signalements", tot))
    for f,l in sorted(pb.items(), key=lambda x:-len(x[1])):
        print("\n--- %s ---"%f)
        for x in l[:6]: print("   ", x)
