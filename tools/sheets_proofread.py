# -*- coding: utf-8 -*-
"""Proofreading batches of WHOLE ARTICLES.

The existing judgement sheets bear on an isolated token, drawn from a
detector. The structural detectors are exhausted: doubled consonant,
impossible ending, impossible initial group, letter lost at the head of a
line -- every one has given what it had. What is left calls for READING the
definition and judging on the sense, article by article.

We therefore write the book out in batches of pure text. No images: the
transcription carries sense enough, and costs twenty times less.
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
