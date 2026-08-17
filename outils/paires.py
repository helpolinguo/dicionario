# -*- coding: utf-8 -*-
"""Correction des sosies, par le lexique du livre lui-meme.

Les planches ont montre que les groupes sont bien etiquetes : les confusions
qui restent sont des cellules isolees tombees dans le mauvais groupe. Elles ne
se voient pas groupe par groupe — elles se voient par le mot.

Un mot du texte qui n'existe pratiquement nulle part ailleurs dans le livre,
mais qui devient un mot bien atteste des qu'on echange deux caracteres que la
machine confond, est une confusion. On n'echange que des caracteres dont les
relecteurs ont constate qu'ils se ressemblent : la correction ne peut donc pas
inventer un mot, seulement retablir une forme que le livre emploie deja.

Le critere est severe et symetrique : la forme corrigee doit compter au moins
six occurrences et etre au moins huit fois plus frequente que la forme fautive.
"""
import numpy as np, sys, re, collections, json
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"
PAIRES = [('c','o'),('c','e'),('e','o'),('i','l'),('i','1'),('l','1'),('n','u'),
          ('r','v'),('b','h'),('s','z'),('s','8'),('m','n'),('a','o'),('a','u'),
          ('t','l'),('g','q'),('f','t'),('d','a'),('p','t'),('k','c'),('x','s'),
          ('m','a'),('h','n'),('v','y'),('j','i'),('O','0'),('I','l'),('S','5'),
          ('m','rn'),('d','cl')]
SOSIE=collections.defaultdict(set)
for a,b in PAIRES:
    if len(a)==1 and len(b)==1: SOSIE[a].add(b); SOSIE[b].add(a)
MINI_ATTESTE=6; MAXI_FAUTIF=2; RAPPORT=8

def executer(sortie=f"{T}/paires.json"):
    from edition import charger_texte
    pages,_,_=charger_texte()
    lignes=[]
    for pg in sorted(pages):
        for k,s in pages[pg]:
            if s.strip(): lignes.append((pg,k,s))
    freq=collections.Counter()
    for _,_,s in lignes:
        for w in re.findall(r"[A-Za-z0-9]{2,}", s): freq[w]+=1
    print("formes distinctes :", len(freq), flush=True)
    prop=[]; vus=set()
    for pg,k,s in lignes:
        for m in re.finditer(r"[A-Za-z0-9]{3,}", s):
            w=m.group(0); n=freq[w]
            if n>MAXI_FAUTIF: continue
            best=None
            for i,ch in enumerate(w):
                for autre in SOSIE.get(ch,()):
                    v=w[:i]+autre+w[i+1:]
                    nv=freq.get(v,0)
                    if nv>=MINI_ATTESTE and nv>=RAPPORT*max(n,1):
                        if best is None or nv>best[2]: best=(i,autre,nv,v)
            if best:
                i,autre,nv,v=best
                cle=(pg,k,m.start()+i)
                if cle in vus: continue
                vus.add(cle)
                prop.append(dict(pagino=pg, ligno=k, kolumno=m.start()+i,
                                 de=w[i], al=autre, fautiva=w, korektita=v,
                                 n_fautiva=n, n_korektita=nv))
    print("corrections proposees :", len(prop), flush=True)
    c=collections.Counter((p['de'],p['al']) for p in prop)
    for (a,b),n in c.most_common(30): print(f"   {a} -> {b} : {n}")
    json.dump(prop, open(sortie,'w'), ensure_ascii=False)

if __name__=="__main__": executer()
