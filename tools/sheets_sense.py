# -*- coding: utf-8 -*-
"""Judgement sheets, the second kind: does the word make sense here?

The first kind proposed a neighbouring form obtained by exchanging
look-alikes. It therefore sees only the slips that have an attested
neighbour. This one proposes nothing: it gives the word and its context, and
asks whether the word exists in Ido in that place. It is the only way to
catch an isolated slip.

We set aside in advance what is plainly legitimate -- the scientific names
announced by « L. » and the proper nouns, recognised by their capital -- so
as not to have judged what does not need judging.
"""
import json, re, sys, os, collections
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from suspects import inventaire
from clean import known, variants
from sheets_judge import context_of
T=_ROOT + "/work"; REP=f"{T}/sens"

def run_step(per=60, batches=10):
    ent,root,inc,ctx,freq=inventaire()
    pool=[]
    for w,n in inc.items():
        if n>2: continue
        if any(known(v,root) for v in set(variants(w))): continue   # seen by the other sheet
        hw,img,ln,idx,s = ctx[w]
        if re.search(r'\bL\.\s*[A-Za-z]', s): continue              # scientific name
        o=re.search(re.escape(w), s, re.I)
        if o and s[o.start():o.start()+1].isupper(): continue       # proper noun
        pool.append((n, w, hw, img, ln, s))
    pool.sort(key=lambda x:(x[0], x[1]))                            # hapax first
    os.makedirs(REP, exist_ok=True)
    records=[dict(id=i, mot=w, ved=hw, img=img, lig=ln, ctx=context_of(s,w))
            for i,(n,w,hw,img,ln,s) in enumerate(pool)]
    json.dump(records, open(f"{REP}/fiches.json","w"), ensure_ascii=False)
    for L in range(batches):
        batch=records[L*per:(L+1)*per]
        if not batch: break
        with open(f"{REP}/lot{L+1:02d}.txt","w",encoding='utf-8') as f:
            for x in batch:
                f.write("%d\t%s\t%s | %s\n"%(x['id'], x['mot'], x['ved'], x['ctx']))
    print("pool %d ; %d lots de %d ecrits"%(len(records), min(batches,(len(records)+per-1)//per), per))

if __name__=="__main__": run_step()
