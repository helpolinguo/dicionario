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
sys.path.insert(0,'/root/dicionario/outils')
from suspects import inventaire
from clean import connu, variantes
T="/root/dicionario/travail"; REP=f"{T}/juger"

def context_of(s, w, large=42):
    m=re.search(r'\b'+re.escape(w)+r'\b', s, re.I)
    if not m: return s[:2*large]
    a=max(0, m.start()-large); b=min(len(s), m.end()+large)
    return ("…" if a else "")+s[a:b]+("…" if b<len(s) else "")

def executer(par=60):
    ent,rac,inc,ctx,freq=inventaire()
    pool=sorted((w,n) for w,n in inc.items()
                if n<=2 and any(connu(v,rac) for v in set(variantes(w))))
    os.makedirs(REP, exist_ok=True)
    fiches=[]
    for i,(w,n) in enumerate(pool):
        ved,img,lig,idx,s = ctx[w]
        vois=sorted({v for v in set(variantes(w)) if connu(v,rac)})[:4]
        fiches.append(dict(id=i, mot=w, vois=vois, ved=ved, img=img, lig=lig,
                           ctx=context_of(s, w)))
    json.dump(fiches, open(f"{REP}/fiches.json","w"), ensure_ascii=False)
    n=0
    for d in range(0, len(fiches), par):
        lot=fiches[d:d+par]; n+=1
        with open(f"{REP}/lot{n:02d}.txt","w",encoding='utf-8') as f:
            for x in lot:
                f.write("%d\t%s\t%s\t%s | %s\n"
                        %(x['id'], x['mot'], ",".join(x['vois']) or "-",
                          x['ved'], x['ctx']))
    print("candidats %d ; lots %d de %d"%(len(fiches), n, par))
    return n

if __name__=="__main__": executer()
