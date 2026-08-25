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
sys.path.insert(0,'/root/dicionario/outils')
from suspects import inventaire
from clean import connu, variantes
from sheets_judge import context_of
T="/root/dicionario/travail"; REP=f"{T}/sens"

def executer(par=60, lots=10):
    ent,rac,inc,ctx,freq=inventaire()
    pool=[]
    for w,n in inc.items():
        if n>2: continue
        if any(connu(v,rac) for v in set(variantes(w))): continue   # seen by the other sheet
        ved,img,lig,idx,s = ctx[w]
        if re.search(r'\bL\.\s*[A-Za-z]', s): continue              # scientific name
        o=re.search(re.escape(w), s, re.I)
        if o and s[o.start():o.start()+1].isupper(): continue       # proper noun
        pool.append((n, w, ved, img, lig, s))
    pool.sort(key=lambda x:(x[0], x[1]))                            # hapax first
    os.makedirs(REP, exist_ok=True)
    fiches=[dict(id=i, mot=w, ved=ved, img=img, lig=lig, ctx=context_of(s,w))
            for i,(n,w,ved,img,lig,s) in enumerate(pool)]
    json.dump(fiches, open(f"{REP}/fiches.json","w"), ensure_ascii=False)
    for L in range(lots):
        lot=fiches[L*par:(L+1)*par]
        if not lot: break
        with open(f"{REP}/lot{L+1:02d}.txt","w",encoding='utf-8') as f:
            for x in lot:
                f.write("%d\t%s\t%s | %s\n"%(x['id'], x['mot'], x['ved'], x['ctx']))
    print("pool %d ; %d lots de %d ecrits"%(len(fiches), min(lots,(len(fiches)+par-1)//par), par))

if __name__=="__main__": executer()
