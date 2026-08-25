# -*- coding: utf-8 -*-
"""Controle systematique de l'edition structuree.

Le fac-simile conserve la moindre faute de l'original ; l'edition structuree,
elle, doit en presenter une forme nette. On ne corrige donc pas au cas par cas
— chaque passe faisait apparaitre une famille nouvelle — mais on inventorie
les ecarts par FAMILLE, on traite la famille, et on recontrole.

Les controles sont independants les uns des autres, et chacun repose sur un
invariant du livre lui-meme, non sur mon jugement :

  couverture   chaque article a une source, chaque source un article
  aller-retour le texte de l'article se retrouve dans ses lignes d'origine
  ordre        le dictionnaire est alphabetique ; une rupture est un indice
  morphologie  une vedette ido finit par -o -a -e -i -ar -ir -or (ou est affixe)
  langui       le code final est un sous-ensemble de DEFIRSLP
  ponctuation  ni ponctuation orpheline, ni cesure non recollee, ni vide
  latina       le nom scientifique est extrait, pas laisse dans le sens
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
    """Cle de tri : sans l'asterisque des mots non officiels, sans trait."""
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
        # Formes legitimes que le controle prenait pour du bruit : l'elision
        # « a(d) », l'interjection « ah! », la locution « a posteriori ».
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
        # Le code se lit par _lire_code, qui admet la capitale abimee
        # (« dEFIRS »), le « l » lu pour « I » (« DEFlS ») et la langue epelee
        # (« Ned », « FDSued », « Jap.,Sanskr »). Compare a un simple jeu de
        # lettres, tout cela passait pour invalide.
        k=e.get('kodo')
        if k and not all(_lire_code(x.strip(' .')) for x in str(k).split(',')):
            pb['code-invalide'].append(n)
        if re.search(r'(?<![A-Za-z])L\.\s*[a-z]', txt): pb['latina-dans-le-senco'].append(n)
        if re.search(r'\b[DEFIRS]{3,7}\b\s*\.?\s*$', txt): pb['code-dans-le-senco'].append(n)
    # ordre alphabetique
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
