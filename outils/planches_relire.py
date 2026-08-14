# -*- coding: utf-8 -*-
"""Lots de relecture d'ARTICLES ENTIERS.

Les planches de jugement existantes portent sur un jeton isole, tire d'un
detecteur. Les detecteurs structurels sont epuises : consonne doublee, finale
impossible, groupe initial impossible, lettre perdue en tete de ligne — tous
ont rendu ce qu'ils avaient. Ce qui reste demande de LIRE la definition et de
juger sur le sens, article par article.

On ecrit donc le livre en lots de texte pur. Aucune image : la transcription
porte assez de sens, et coute vingt fois moins.
"""
import json, os, sys
T = "/root/dicionario/travail"
LOT = 130


def ecrire(source=f"{T}/edicioni/dicionario.jsonl", dossier=f"{T}/relire/loti"):
    os.makedirs(dossier, exist_ok=True)
    ent = [json.loads(l) for l in open(source, encoding='utf-8')]
    n = 0
    for i in range(0, len(ent), LOT):
        n += 1
        with open(f"{dossier}/l{n:03d}.txt", "w", encoding='utf-8') as f:
            for j, e in enumerate(ent[i:i+LOT]):
                idx = i + j
                fa = f"({e['fako']}) " if e['fako'] else ""
                f.write("%d\t%s\t%s%s\n" % (idx, e['vedetto'], fa,
                                            " | ".join(e['senci'])))
    print("%d lots de %d articles dans %s" % (n, LOT, dossier))
    return n


if __name__ == "__main__":
    ecrire()
