# -*- coding: utf-8 -*-
"""A check on the yield of the proofreading.

The book runs at around sixteen corrections a page. A page that returns zero
or one has probably not been read: the two pages of the Prefaco came back
empty, and they were faulty. We therefore watch the count, rather than
discover it through the reader.
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
    # Since page 96, the underlines are no longer surveyed by hand:
    # the automatic detection takes care of them. Their absence is therefore
    # not a defect.
    pass
    return [p for p,_,_ in maigres]+sans_sou

if __name__=="__main__":
    a=executer()
    print("\na refaire :", " ".join("%03d"%p for p in sorted(set(a))))
