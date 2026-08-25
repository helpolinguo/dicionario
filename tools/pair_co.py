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
import os
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,_ROOT + "/tools")
T=_ROOT + "/work"
MIN_ATTESTED = 6      # minimum occurrences of the corrected form
MAX_FAULTY  = 2      # maximum occurrences of the faulty form

def run_step():
    from edition import load_text
    pages,_,_=load_text()
    lines=[]
    for pg in sorted(pages):
        for k,s in pages[pg]:
            if s.strip(): lines.append((pg,k,s))
    freq=collections.Counter()
    for _,_,s in lines:
        for w in re.findall(r"[A-Za-z]{2,}", s): freq[w]+=1
    print("formes distinctes :", len(freq), flush=True)
    prop=[]
    for pg,k,s in lines:
        for m in re.finditer(r"[A-Za-z]{3,}", s):
            w=m.group(0); n=freq[w]
            if n>MAX_FAULTY: continue
            for i,ch in enumerate(w):
                if ch not in "co": continue
                other = 'o' if ch=='c' else 'c'
                v = w[:i]+other+w[i+1:]
                nv=freq.get(v,0)
                if nv>=MIN_ATTESTED and nv>=8*max(n,1):
                    prop.append(dict(pagino=pg, ligno=k, kolumno=m.start()+i,
                                     fautiva=w, korektita=v, n_fautiva=n, n_korektita=nv))
                    break
    print("confusions c/o proposees :", len(prop), flush=True)
    c=collections.Counter((p['fautiva'],p['korektita']) for p in prop)
    for (a,b),n in c.most_common(25): print(f"   {a} -> {b}  ({n} fois)")
    json.dump(prop, open(f"{T}/paire_co.json","w"), ensure_ascii=False)

if __name__=="__main__": run_step()
