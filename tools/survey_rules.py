# -*- coding: utf-8 -*-
"""Releve des soulignements que l'edition n'a pas su placer.

Le tapuscrit n'a pas d'italique : la dactylo souligne. L'edition lit ces filets
et en fait l'italique du domaine, le gras de la locution. Certains filets ne se
laissent pas placer : le trait deborde sur la ponctuation, s'arrete a la moitie
d'un mot, ou ne couvre qu'un mot-outil. Ce sont des artefacts du releve, non des
intentions de l'auteur — mais il faut pouvoir en juger.

Le fichier rendu les classe par famille, la plus douteuse en tete, avec la page
et le mot-vedette pour aller voir le fac-simile.

    python3 tools/survey_rules.py
"""
import json, os, re, sys, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edition

RAC = "/root/dicionario"
SOURCE = f"{RAC}/dicionario.jsonl"
SORTIE = f"{RAC}/filets-dubinda.md"

# La liste des mots-outils est celle de l'edition, `edition.MALGRANDA` : c'est
# elle qui decide de ne PAS poser l'italique, et la liste de travail doit
# classer d'apres la meme regle, sans quoi les fragments qu'elle ecarte se
# retrouvent ici dans une autre famille que la leur.


def famille(u):
    """A quoi ressemble le fragment ?"""
    mots = u.split()
    if len(u) <= 3:
        return "2. Fragment de trois lettres ou moins"
    if not re.fullmatch(r"[A-Za-zÀ-ÿ'’ .,()-]+", u):
        return "2. Fragment de trois lettres ou moins"
    if edition._nur_motouti(u):
        return "3. Mots-outils seuls"
    if u[0].isupper() and len(mots) <= 4:
        return "1. Ressemble a un qualificatif ou a une locution"
    return "4. Coupe au milieu d'un mot, ou reste du mot-vedette"


def ecrire(source=SOURCE, sortie=SORTIE):
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    par = collections.defaultdict(list)
    for e in ent:
        for u in e.get('dubinda', []):
            par[famille(u)].append((e['pagino'], e['vedetto'], u))
    total = sum(len(v) for v in par.values())
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
    for fam in sorted(par):
        v = sorted(par[fam])
        L += [f"## {fam[3:]} — {len(v)}", "",
              "| page | mot-vedette | fragment souligne |",
              "|---:|---|---|"]
        for p, ved, u in v:
            L.append(f"| {p} | {ved} | `{u}` |")
        L.append("")
    open(sortie, "w", encoding='utf-8').write("\n".join(L) + "\n")
    return total, {k: len(v) for k, v in par.items()}


if __name__ == "__main__":
    n, d = ecrire()
    print("fragments non places :", n)
    for k in sorted(d):
        print("   %-58s %d" % (k, d[k]))
