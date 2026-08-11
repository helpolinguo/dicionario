# -*- coding: utf-8 -*-
"""Reperage des confusions c/o restantes, par le lexique du livre lui-meme.

Les planches ont montre que les groupes etiquetes « c » et « o » sont bien
etiquetes : la confusion signalee ne vient donc pas de l'etiquette du groupe
mais de cellules isolees, tombees dans le mauvais groupe. On ne peut pas les
voir groupe par groupe ; on les voit par le mot.

Un mot du corps du texte qui n'existe nulle part ailleurs dans le livre, mais
qui devient un mot atteste des qu'on echange un « c » et un « o », est une
confusion. Le critere est severe : la forme corrigee doit etre nettement plus
frequente que la forme fautive, faute de quoi on ne conclut pas.
"""
import numpy as np, sys, re, collections, json
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"
MINI_ATTESTE = 6      # occurrences minimales de la forme corrigee
MAXI_FAUTIF  = 2      # occurrences maximales de la forme fautive

def executer():
    from edition import charger_texte
    pages,_=charger_texte()
    lignes=[]
    for pg in sorted(pages):
        for k,s in pages[pg]:
            if s.strip(): lignes.append((pg,k,s))
    freq=collections.Counter()
    for _,_,s in lignes:
        for w in re.findall(r"[A-Za-z]{2,}", s): freq[w]+=1
    print("formes distinctes :", len(freq), flush=True)
    prop=[]
    for pg,k,s in lignes:
        for m in re.finditer(r"[A-Za-z]{3,}", s):
            w=m.group(0); n=freq[w]
            if n>MAXI_FAUTIF: continue
            for i,ch in enumerate(w):
                if ch not in "co": continue
                autre = 'o' if ch=='c' else 'c'
                v = w[:i]+autre+w[i+1:]
                nv=freq.get(v,0)
                if nv>=MINI_ATTESTE and nv>=8*max(n,1):
                    prop.append(dict(pagino=pg, ligno=k, kolumno=m.start()+i,
                                     fautiva=w, korektita=v, n_fautiva=n, n_korektita=nv))
                    break
    print("confusions c/o proposees :", len(prop), flush=True)
    c=collections.Counter((p['fautiva'],p['korektita']) for p in prop)
    for (a,b),n in c.most_common(25): print(f"   {a} -> {b}  ({n} fois)")
    json.dump(prop, open(f"{T}/paire_co.json","w"), ensure_ascii=False)

if __name__=="__main__": executer()
