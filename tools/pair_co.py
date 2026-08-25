# -*- coding: utf-8 -*-
"""Locating the c/o confusions that remain, by the book's own lexicon.

The sheets have shown that the groups labelled « c » and « o » are labelled
rightly: the confusion reported therefore comes not from the group's label
but from isolated cells that have fallen into the wrong group. They cannot be
seen group by group; they are seen through the word.

A word in the body of the text that exists nowhere else in the book, but that
becomes an attested word as soon as a « c » and an « o » are exchanged, is a
confusion. The criterion is severe: the corrected form must be markedly more
frequent than the faulty one, failing which we draw no conclusion.
"""
import numpy as np, sys, re, collections, json
sys.path.insert(0,'/root/dicionario/outils')
T="/root/dicionario/travail"
MINI_ATTESTE = 6      # minimum occurrences of the corrected form
MAXI_FAUTIF  = 2      # maximum occurrences of the faulty form

def executer():
    from edition import charger_texte
    pages,_,_=charger_texte()
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
