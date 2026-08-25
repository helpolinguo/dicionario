# -*- coding: utf-8 -*-
"""Planches de jugement, en texte seul.

Le scan est use et cher a lire ; la transcription, elle, se lit pour rien. On
ne soumet donc ni images ni pages entieres, mais la seule question qui reste
ouverte : ce mot fait-il sens en ido a cet endroit ?

Une ligne par candidat : numero, forme lue, formes voisines obtenues par
echange de sosies, et le contexte strictement necessaire. Le juge repond par
le numero et la forme retenue, rien d'autre.
"""
import json, re, sys, os, collections
sys.path.insert(0,'/root/dicionario/outils')
from suspects import inventaire
from clean import connu, variantes
T="/root/dicionario/travail"; REP=f"{T}/juger"

def contexte(s, w, large=42):
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
                           ctx=contexte(s, w)))
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
