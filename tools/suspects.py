# -*- coding: utf-8 -*-
"""An inventory of the words to be put to judgement, and nothing else.

The scan does not settle it -- it is too worn -- and re-reading it is
expensive. What settles it is knowing whether a word makes sense in Ido. We
therefore do not submit the whole book: we submit only the words whose root
is attested nowhere as a headword, and which are not function words. The
rest of the text does not need to be read to be judged sound.
"""
import json, re, sys, collections
sys.path.insert(0,'/root/dicionario/outils')
from clean import racines, connu, MOT, variantes
T="/root/dicionario/travail"

def inventaire():
    ent=[json.loads(l) for l in open(f"{T}/edicioni/dicionario.jsonl",encoding='utf-8')]
    rac=racines(ent)
    freq=collections.Counter(); ctx={}
    for e in ent:
        for i,s in enumerate(e.get('senci') or []):
            for w in MOT.findall(s):
                b=w.lower()
                freq[b]+=1
                if b not in ctx: ctx[b]=(e['vedetto'], e['image'], e['ligno'], i, s)
    inc={w:n for w,n in freq.items() if not connu(w,rac)}
    return ent, rac, inc, ctx, freq

if __name__=="__main__":
    ent,rac,inc,ctx,freq=inventaire()
    print("articles %d | racines connues %d"%(len(ent),len(rac)))
    print("formes distinctes dans les definitions : %d"%len(freq))
    print("formes a racine inconnue : %d (occurrences %d)"%(len(inc),sum(inc.values())))
    par=collections.Counter()
    for w,n in inc.items(): par[min(n,4)]+=1
    print("  dont hapax : %d | 2 fois : %d | 3 fois : %d | 4+ : %d"
          %(par[1],par[2],par[3],par[4]))
    avec=sum(1 for w in inc if any(connu(v,rac) for v in set(variantes(w))))
    print("  dont un echange de sosies suffit a rendre connues : %d"%avec)
