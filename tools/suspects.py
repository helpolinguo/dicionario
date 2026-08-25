# -*- coding: utf-8 -*-
"""An inventory of the words to be put to judgement, and nothing else.

The scan does not settle it -- it is too worn -- and re-reading it is
expensive. What settles it is knowing whether a word makes sense in Ido. We
therefore do not submit the whole book: we submit only the words whose root
is attested nowhere as a headword, and which are not function words. The
rest of the text does not need to be read to be judged sound.
"""
import json, re, sys, collections
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from clean import roots, known, WORD, variants
T=_ROOT + "/work"

def inventory():
    ent=[json.loads(l) for l in open(f"{T}/editions/dicionario.jsonl",encoding='utf-8')]
    root=roots(ent)
    freq=collections.Counter(); ctx={}
    for e in ent:
        for i,s in enumerate(e.get('senci') or []):
            for w in WORD.findall(s):
                b=w.lower()
                freq[b]+=1
                if b not in ctx: ctx[b]=(e['vedetto'], e['image'], e['ligno'], i, s)
    inc={w:n for w,n in freq.items() if not known(w,root)}
    return ent, root, inc, ctx, freq

if __name__=="__main__":
    ent,root,inc,ctx,freq=inventory()
    print("articles %d | roots known %d"%(len(ent),len(root)))
    print("distinct forms in the definitions: %d"%len(freq))
    print("formes a racine inconnue : %d (occurrences %d)"%(len(inc),sum(inc.values())))
    per=collections.Counter()
    for w,n in inc.items(): per[min(n,4)]+=1
    print("  dont hapax : %d | 2 fois : %d | 3 fois : %d | 4+ : %d"
          %(per[1],per[2],per[3],per[4]))
    with_arg=sum(1 for w in inc if any(known(v,root) for v in set(variants(w))))
    print("  of which one exchange of look-alikes makes known: %d"%with_arg)
