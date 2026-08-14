# -*- coding: utf-8 -*-
"""Planches de jugement, seconde espece : le mot fait-il sens ici ?

La premiere espece proposait une forme voisine obtenue par echange de sosies.
Elle ne voit donc que les coquilles qui ont un voisin atteste. Celle-ci ne
propose rien : elle donne le mot et son contexte, et demande si le mot existe
en ido a cet endroit. C'est le seul moyen d'attraper une coquille isolee.

On ecarte d'avance ce qui est manifestement legitime — les noms scientifiques
annonces par « L. » et les noms propres, reconnus a leur capitale — pour ne pas
faire juger ce qui n'a pas besoin de l'etre.
"""
import json, re, sys, os, collections
sys.path.insert(0,'/root/dicionario/outils')
from suspects import inventaire
from netigar import connu, variantes
from planches_juger import contexte
T="/root/dicionario/travail"; REP=f"{T}/sens"

def executer(par=60, lots=10):
    ent,rac,inc,ctx,freq=inventaire()
    pool=[]
    for w,n in inc.items():
        if n>2: continue
        if any(connu(v,rac) for v in set(variantes(w))): continue   # vu par l'autre planche
        ved,img,lig,idx,s = ctx[w]
        if re.search(r'\bL\.\s*[A-Za-z]', s): continue              # nom scientifique
        o=re.search(re.escape(w), s, re.I)
        if o and s[o.start():o.start()+1].isupper(): continue       # nom propre
        pool.append((n, w, ved, img, lig, s))
    pool.sort(key=lambda x:(x[0], x[1]))                            # hapax d'abord
    os.makedirs(REP, exist_ok=True)
    fiches=[dict(id=i, mot=w, ved=ved, img=img, lig=lig, ctx=contexte(s,w))
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
