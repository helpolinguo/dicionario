# -*- coding: utf-8 -*-
"""Judgement sheets, in text alone.

The scan is worn and expensive to read; the transcription reads for nothing.
We therefore submit neither images nor whole pages, but the one question
left open: does this word make sense in Ido in this place?

One line per candidate: number, form read, neighbouring forms obtained by
exchanging look-alikes, and the strictly necessary context. The judge
answers with the number and the form chosen, nothing else.
"""
import json, re, sys, os, collections
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
from suspects import inventory
from clean import known, variants
T=_ROOT + "/work"; REP=f"{T}/juger"

def context_of(s, w, large=42):
    m=re.search(r'\b'+re.escape(w)+r'\b', s, re.I)
    if not m: return s[:2*large]
    a=max(0, m.start()-large); b=min(len(s), m.end()+large)
    return ("…" if a else "")+s[a:b]+("…" if b<len(s) else "")

def run_step(per=60):
    ent,root,inc,ctx,freq=inventory()
    pool=sorted((w,n) for w,n in inc.items()
                if n<=2 and any(known(v,root) for v in set(variants(w))))
    os.makedirs(REP, exist_ok=True)
    records=[]
    for i,(w,n) in enumerate(pool):
        hw,img,ln,idx,s = ctx[w]
        neigh=sorted({v for v in set(variants(w)) if known(v,root)})[:4]
        records.append(dict(id=i, mot=w, vois=neigh, ved=hw, img=img, lig=ln,
                           ctx=context_of(s, w)))
    json.dump(records, open(f"{REP}/fiches.json","w"), ensure_ascii=False)
    n=0
    for d in range(0, len(records), per):
        batch=records[d:d+per]; n+=1
        with open(f"{REP}/lot{n:02d}.txt","w",encoding='utf-8') as f:
            for x in batch:
                f.write("%d\t%s\t%s\t%s | %s\n"
                        %(x['id'], x['mot'], ",".join(x['vois']) or "-",
                          x['ved'], x['ctx']))
    print("candidats %d ; lots %d de %d"%(len(records), n, per))
    return n

if __name__=="__main__": run_step()
