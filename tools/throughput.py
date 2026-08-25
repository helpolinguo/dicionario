# -*- coding: utf-8 -*-
"""Controle de rendement de la relecture.

Le livre tourne autour de seize corrections par page. Une page qui en rend
zero ou une n'a probablement pas ete lue : les deux pages de la Prefaco
etaient revenues vides, et elles etaient fautives. On surveille donc le
compte, plutot que de le decouvrir par le lecteur.
"""
import os, glob, sys
T="/root/dicionario/work/relecture"

def executer(seuil=3):
    lignes={}; sou={}
    for f in sorted(glob.glob(f"{T}/rez/p*.txt")):
        pg=int(os.path.basename(f)[1:4]); n=0
        for l in open(f,encoding='utf-8'):
            if l.startswith("#"): break
            if "|" in l: n+=1
        lignes[pg]=n
    for f in sorted(glob.glob(f"{T}/rez/p*.sou")):
        pg=int(os.path.basename(f)[1:4])
        sou[pg]=sum(1 for l in open(f,encoding='utf-8') if "|" in l and not l.startswith("#"))
    import statistics as st
    v=sorted(lignes.values())
    print(f"pages relues : {len(lignes)} ; lignes corrigees : mediane {st.median(v)}, total {sum(v)}")
    maigres=[(p,n,sou.get(p,0)) for p,n in sorted(lignes.items()) if n<seuil]
    sans_sou=[p for p in lignes if p not in sou]
    print(f"pages a moins de {seuil} corrections : {len(maigres)}")
    for p,n,s in maigres: print(f"   p-{p:03d} : {n} lignes corrigees, {s} lignes soulignees")
    # Depuis la page 96, les soulignements ne sont plus releves a la main :
    # la detection automatique s'en charge. Leur absence n'est donc pas un defaut.
    pass
    return [p for p,_,_ in maigres]+sans_sou

if __name__=="__main__":
    a=executer()
    print("\na refaire :", " ".join("%03d"%p for p in sorted(set(a))))
